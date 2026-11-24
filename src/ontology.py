"""Načítanie OWL ontológie Cukráreň a jej prevod na fakty a graf.

Ontológia sa v RAG používa na dvoch miestach:
  1. pri indexovaní: každý chunk z PDF sa označí pojmami z ontológie, ktoré obsahuje,
  2. pri otázke: pojmy nájdené v otázke sa rozšíria o susedov v ontológii a ich fakty
     (napr. Tiramisu -> je Dessert -> hasIngredient DairyProduct) sa pridajú do promptu.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import networkx as nx
import rdflib
from rdflib import OWL, RDF, RDFS, BNode, Literal, URIRef
from rdflib.collection import Collection

from config import LABELS_SK_FILE, ONTOLOGY_FILE, SYNONYMS_FILE


def _split_camel(name: str) -> str:
    """'PastryChef' -> 'pastry chef'"""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).lower()


@dataclass
class Ontology:
    graph: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)
    facts: dict[str, list[str]] = field(default_factory=dict)  # pojem -> vety o ňom
    patterns: dict[str, re.Pattern] = field(default_factory=dict)  # pojem -> regex na hľadanie v texte
    rdf: object = None          # pôvodný rdflib graf (pre SPARQL dotazy)
    labels_sk: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ hľadanie
    def find_concepts(self, text: str) -> list[str]:
        """Vráti pojmy ontológie, ktoré sa vyskytujú v texte."""
        return [c for c, p in self.patterns.items() if p.search(text)]

    def neighbours(self, concepts: list[str], depth: int = 1) -> set[str]:
        out = set(concepts)
        frontier = set(concepts)
        for _ in range(depth):
            nxt = set()
            for c in frontier:
                if c in self.graph:
                    nxt |= set(self.graph.successors(c)) | set(self.graph.predecessors(c))
            out |= nxt
            frontier = nxt
        return out

    def context_for(self, concepts: list[str]) -> str:
        """Fakty z ontológie o daných pojmoch (bez duplikátov)."""
        seen, lines = set(), []
        for c in concepts:
            for f in self.facts.get(c, []):
                if f not in seen:
                    seen.add(f)
                    lines.append(f)
        return "\n".join(lines)


def load_ontology(path=ONTOLOGY_FILE) -> Ontology:
    g = rdflib.Graph().parse(str(path))
    onto = Ontology()
    onto.rdf = g

    def label(node) -> str:
        if isinstance(node, Literal):
            return str(node)
        lab = g.value(node, RDFS.label)
        if lab:
            return str(lab)
        s = str(node)
        return s.split("#")[-1].split("/")[-1]

    labels_sk = json.loads(LABELS_SK_FILE.read_text(encoding="utf-8")) if LABELS_SK_FILE.exists() else {}
    onto.labels_sk = labels_sk

    def disp(name: str) -> str:
        """'PastryChef' -> 'PastryChef (cukrár)' – LLM tak nemusí prekladať anglické názvy tried."""
        return f"{name} ({labels_sk[name]})" if name in labels_sk else name

    def add_edge(s: str, rel: str, o: str, kind: str = "relation"):
        onto.graph.add_edge(s, o, label=rel, kind=kind)
        fact = f"{disp(s)} {rel} {disp(o)}."
        for c in (s, o):
            onto.facts.setdefault(c, [])
            if fact not in onto.facts[c]:
                onto.facts[c].append(fact)

    # --- uzly: triedy a indivíduá
    for c in g.subjects(RDF.type, OWL.Class):
        if isinstance(c, URIRef):
            onto.graph.add_node(label(c), kind="class")
    for i in g.subjects(RDF.type, OWL.NamedIndividual):
        onto.graph.add_node(label(i), kind="individual")

    # --- reštrikcie (hasIngredient some Flour, ...)
    def restriction_to_edge(cls: str, r: BNode):
        prop = g.value(r, OWL.onProperty)
        if prop is None:
            return
        p = label(prop)
        if (o := g.value(r, OWL.someValuesFrom)) is not None and isinstance(o, URIRef):
            add_edge(cls, p, label(o))
        elif (o := g.value(r, OWL.onClass)) is not None:
            for card, word in ((OWL.qualifiedCardinality, "exactly"),
                               (OWL.minQualifiedCardinality, "at least"),
                               (OWL.maxQualifiedCardinality, "at most")):
                if (n := g.value(r, card)) is not None:
                    add_edge(cls, f"{p} ({word} {n})", label(o))
        elif (o := g.value(r, OWL.onDataRange)) is not None:
            onto.facts.setdefault(cls, []).append(f"{cls} has data property {p} of type {label(o)}.")

    def handle_class_expr(cls: str, expr):
        if isinstance(expr, URIRef):
            add_edge(cls, "is a", label(expr), kind="subclass")
        elif (g.value(expr, RDF.type) == OWL.Restriction):
            restriction_to_edge(cls, expr)
        elif (lst := g.value(expr, OWL.intersectionOf)) is not None:
            for part in Collection(g, lst):
                handle_class_expr(cls, part)

    for s, o in g.subject_objects(RDFS.subClassOf):
        if isinstance(s, URIRef):
            handle_class_expr(label(s), o)
    for s, o in g.subject_objects(OWL.equivalentClass):
        if isinstance(s, URIRef):
            handle_class_expr(label(s), o)

    # --- vlastnosti: domain / range
    for p in g.subjects(RDF.type, OWL.ObjectProperty):
        d, r = g.value(p, RDFS.domain), g.value(p, RDFS.range)
        if isinstance(d, URIRef) and isinstance(r, URIRef):
            fact = f"Relation {label(p)} connects {disp(label(d))} to {disp(label(r))}."
            for c in (label(d), label(r)):
                onto.facts.setdefault(c, []).append(fact)

    # --- indivíduá: typ, objektové a dátové vlastnosti
    skip = {RDF.type, RDFS.label, RDFS.comment}
    for i in g.subjects(RDF.type, OWL.NamedIndividual):
        name = label(i)
        for t in g.objects(i, RDF.type):
            if t != OWL.NamedIndividual and isinstance(t, URIRef):
                add_edge(name, "instance of", label(t), kind="instance")
        for p, o in g.predicate_objects(i):
            if p in skip:
                continue
            if isinstance(o, Literal):
                onto.facts.setdefault(name, []).append(f"{name} {label(p)} {o}.")
                onto.graph.nodes[name].setdefault("data", {})[label(p)] = str(o)
            elif isinstance(o, URIRef):
                add_edge(name, label(p), label(o))

    for c, txt in ((label(s), str(o)) for s, o in g.subject_objects(RDFS.comment)
                   if (s, RDF.type, OWL.Class) in g):
        onto.facts.setdefault(c, []).insert(0, f"{c}: {txt}")

    # --- vzory na hľadanie pojmov v texte (anglický názov + slovenské synonymá)
    synonyms = {}
    if SYNONYMS_FILE.exists():
        synonyms = json.loads(SYNONYMS_FILE.read_text(encoding="utf-8"))
    for node, data in onto.graph.nodes(data=True):
        if data.get("kind") != "class":
            continue
        syn = synonyms.get(node, [])
        terms = {_split_camel(node), node.lower()} | {s.lower() for s in syn if not s.startswith("re:")}
        # synonymum "re:..." je priamo regulárny výraz (napr. na odlíšenie cukrár / cukráreň)
        alts = [re.escape(t) for t in terms] + [s[3:] for s in syn if s.startswith("re:")]
        # slovo môže pokračovať koncovkou (torta, torty, tortu ...)
        alt = "|".join(sorted(alts, key=len, reverse=True))
        onto.patterns[node] = re.compile(rf"\b(?:{alt})\w*", re.IGNORECASE)
    return onto


if __name__ == "__main__":
    o = load_ontology()
    print(f"uzly: {o.graph.number_of_nodes()}, hrany: {o.graph.number_of_edges()}")
    for c in ("Tiramisu", "Order"):
        print(f"\n--- {c}\n" + o.context_for([c]))
    print("\nnájdené:", o.find_concepts("Aké suroviny treba na tiramisu a čokoládovú tortu?"))
