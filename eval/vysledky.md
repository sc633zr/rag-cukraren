# Výsledky testovacích otázok

Model: `qwen3:4b-instruct` · 2026-11-23 21:18 · chunkov v indexe: 346


## 1. [ontológia] Aké druhy zamestnancov pracujú v cukrárni?

- pojmy z ontológie: Cukraren, Employee
- nájdené zdroje: sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.51 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.64 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.52 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.68 (0.03)
- čas: 453 s

PastryChef (cukrár), Cashier (pokladník), Manager (manažér) a Baker (pekár).

---  
Zdôvodnenie:  
- PastryChef, Cashier, Manager a Baker sú uvedené ako typy zamestnancov v ontológii.  
- Každý z týchto typov je spojený so Cukraren1 cez reláciu "employs".  
- Žiadna iná kategória alebo úloha nieje uvedená ako pracujúca vo výrobe podľa dostupných dát.


## 2. [ontológia] Aké platobné metódy môže zákazník použiť?

- pojmy z ontológie: Customer, PaymentMethod
- nájdené zdroje: sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.67 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.4 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.53 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.60 (0.03)
- čas: 396 s

Aké platobné metódy môže zákazník použiť?  
Platobné metódy, ktoré môže zákazník použiť, sú: platba kartou a platba v hotovosti.

---  
Zdôvodnenie:  
- V kontexte je uvedené, že „Card (platba kartou) is a PaymentMethod“ a „Cash (platba v hotovosti) is a PaymentMethod“.  
- Tieto dve metódy sú explicitne definované ako spôsoby platby.  
- V dokumente nie je uvedených iných možných spôsobov platby, preto sa základné informácie odvíjajú len zo špecifikácií ontológie a úryvkov.


## 3. [ontológia] Kto pripravil cheesecake a koľko stojí?

- pojmy z ontológie: Cheesecake
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03)
- čas: 409 s

Anna pripravila cheesecake, ktorý stojí 6,50 €.  

---  
Zdôvodnenie:  
- Cheesecake1 preparedBy Anna [ontológia].  
- Cheesecake1 hasPrice 6,50 [ontológia].  
Ceny z ontológie sú použité podľa "CENY NAŠEJ CUKRÁRNE".


## 4. [ontológia] Aké druhy koláčov (Cake) cukráreň ponúka?

- pojmy z ontológie: Cukraren, Cake
- nájdené zdroje: sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.69 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.4 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.7 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.14 (0.03)
- čas: 245 s

ChocolateCake1, DanishPastry, Cheesecake, FruitCake, CarrotCake

---  
Zdôvodnenie:  
- ChocolateCake1 je uvedený ako výrobok cukrárne a je typom torty/koláča (ontológia).  
- DanishPastry je zameraný na pečivo pripravované pracovníkmi, čo sa prenosi do kategórie koláčov.  
- Cheesecake, FruitCake a CarrotCake sú v ontológie uvedené ako typy tort (cake).  
- V dokumentoch nie je explicitne pomenovaný sortiment koláčov, ale z úryvku o recepte pre "koláčik" sa odvodzuje, že existujú rôzne druhy.  
- Z ontológie sú uvedené len typy tort (cake), nie však konkrétne názvy koláčov ako zloženie – preto odpoveď je ohraničená na to, čo je v ontológii definovaných.


## 5. [ontológia] Čo musí obsahovať každá objednávka?

- pojmy z ontológie: Order
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.7 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.6 (0.02)
- čas: 186 s

Každá objednávka musí obsahovať aspoň jeden výrobok, má presne jednu metódu platby a je zpracovaná presne jedním zamestnancom.  

---  
Zdôvodnenie:  
- Order (objednávka) containsProduct (aspoň 1) Product (výrobok) [ontológia].  
- Order (objednávka) hasPaymentMethod (presne 1) PaymentMethod [ontológia].  
- Order (objednávka) processedBy (presne 1) Employee [ontológia].  
V dokumentoch nie je uvedené, čo konkrétne musí byť v objednávke ako obsah alebo podmienky – len spomenuté zásady pre dodávanie a kvalitu.


## 6. [ontológia] Koľko stojí tiramisu?

- pojmy z ontológie: Tiramisu
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.13 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03)
- čas: 193 s

5,90 €

---  
Zdôvodnenie:  
- V "CENY NAŠEJ CUKRÁRNE" (ontológia) je uvedená cena za tiramisu (Tiramisu1): 5,90 € [ontológia].  
- Tento produkt v ponuke našej cukrárne máme podľa zoznamu cien.  
- V úryvku dokumentu sa tiež spomínajú poháre tiramisu a jeho zloženie, ale cena je uvedená len vo "CENY NAŠEJ CUKRÁRNE".


## 7. [dokumenty] Z čoho sa vyrába zmrzlina?

- pojmy z ontológie: IceCream
- nájdené zdroje: sk_Zmrzlina.pdf s.2 (0.03); sk_Zmrzlina.pdf s.2 (0.03); sk_Zmrzlina.pdf s.3 (0.03); sk_Zmrzlina.pdf s.1 (0.03)
- čas: 297 s

Z mrzliny sa vyrábajú z mlieka, smotany (šľahačky), cukru a prísad ako napr. vanilka, guárov gumu, stabilizátory alebo aromatické látky.

---
Zdôvodnenie:
- Z dokumentu [sk_Zmrzlina.pdf, s. 2]: "Býval to mliečny výrobok z mlieka a smotany" – uvedená suroviny (mlieko, smotana).
- Dôležitá je aj prítomnosť cukru: "zmrzlina sa odporúča pri nechutenstve", čo naznačuje výskyt cukru ako ingrediencie [s. 2].
- V úryvku [sk_Zmrzlina.pdf, s. 3] je uvedená vanilka (pripravené zmrzliny obsahujú prípravky so sušeným mliekom a guárovou gumou), čo sa považuje za prísady [s. 2].
- V ontológii je uvedené, že IceCream má ingrediencie: Milk (mlieko), Cream (smotana/šľahačka) a Sugar (cukor).


## 8. [dokumenty] Ako sa vyrába čokoláda z kakaových bôbov?

- pojmy z ontológie: Chocolate, Cocoa
- nájdené zdroje: sk_Cokolada.pdf s.1 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.4 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.4 (0.03); sk_Cokolada.pdf s.2 (0.03)
- čas: 226 s

Čokoládu sa vyrábajú zo zrniek tropického kakaového stromu Theobroma cacao [sk_Cokolada.pdf, s. 1]. Po drvení a valcovaní sa kakaové bôby konšovať a správne miešať, čo určuje kvalitu výrobku [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 4].  

---  
Zdôvodnenie:  
- Zdroj uvádzajú, že čokoláda je vyrobená z plodov kakaovníka (zrniek) [sk_Cokolada.pdf, s. 1].  
- Opisuje postup výrobku od drvenia cez valcovanie a konšovanie [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 4].  
- Správne miešanie je uvedené ako dôležité pre kvalitu čokolády [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 4].


## 9. [dokumenty] Ako sa temperuje čokoláda a pri akých teplotách?

- pojmy z ontológie: Chocolate
- nájdené zdroje: sk_SPPK_cokolada_temperovanie_pralinky.pdf s.5 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.6 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.5 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.6 (0.03)
- čas: 293 s

Čokoládu sa môže temperovať pomocou mikrovlnnej rúry, vodného kúpeľa alebo na kameni. Pri temperovaní sa čokoláda rozpušťa približne na 45 °C a potom teplotu znížime na 28–30 °C [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 6]. Pri vodnom kúpeli je dôležité, aby sa voda nedostala do čokolády a nevarila [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 5]. Skúšku teploty robíme teplomerom alebo cuk.kartou [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 6].

---  
Zdôvodnenie:  
- Temperovanie pomocou mikrovlnnej rúry – čokoláda sa rozpustí pri teplote z vnútra a je potrebné miestne premiešať [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 5].  
- Temperovanie na kameni: čokoládu vylejeme na 45 °C a teplotu znížime na 28–30 °C [sk_SPPK_cokolada_temperovanie_pralinky.pdf, s. 6].  
- Vodný kúpel: je potrebné dbať, aby sa voda nedostala do čokolády a nevarila [sk_SPPK_cokolada_temperovanie_pral


## 10. [dokumenty] V akom pomere sa mieša čokoláda a smotana pri príprave ganache?

- pojmy z ontológie: Chocolate, Cream
- nájdené zdroje: sk_SPPK_ganache.pdf s.3 (0.03); sk_SPPK_ganache.pdf s.2 (0.03); sk_SPPK_ganache.pdf s.3 (0.03); sk_SPPK_ganache.pdf s.1 (0.03)
- čas: 313 s

Pomer čokolády a smotany pri príprave ganache zmenší sa podľa druhu čokolády: pre biele alebo mliečnu čokoládu je pomer 3:1, pre horkú čokoládu je to 2:1. Pre hustý krém (plnku) sa používa pomer 2:1 (dve diely čokolády k jednému dielu smotany).  

---  
Zdôvodnenie:  
- [sk_SPPK_ganache.pdf, s. 3]: "Pri bielej a mliečnej čokoláde je pomer 2 :1 , diely čokolády a jeden diel smotany na šľahanie" – pre horkú čokoládu.  
- [sk_SPPK_ganache.pdf, s. 3]: "Ganache z bielej čokolády - Ganache si pripravíme v pomere 3:1 , z troch dielov bielej čokolády a jedného dielu šľahačkovej smotany" – pre bielu čokoládu.  
- [sk_SPPK_ganache.pdf, s. 2]: "Zvyčajne sa dva diely čokolády a jeden diel smotany používajú na plnenie koláčov alebo ako základ..." – pre hustý krém (plnku).  
- [sk_SPPK_ganache.pdf, s. 1]: "ganache je čokoládový prípravok... pričom sa smotana najskôr zoh


## 11. [dokumenty] Ktoré sú najznámejšie francúzske dezerty?

- pojmy z ontológie: Dessert
- nájdené zdroje: sk_SPPK_francuzske_dezerty.pdf s.2 (0.03); sk_SPPK_francuzske_dezerty.pdf s.1 (0.03); sk_SPPK_francuzske_dezerty.pdf s.1 (0.03); sk_SPPK_francuzske_dezerty.pdf s.1 (0.03)
- čas: 207 s

Najznámejšie francúzske dezerty sú Creme brulée, Palacinka, Makronky, Mousse, Opera, Paris–Brest a Profiteroly [sk_SPPK_francuzske_dezerty.pdf, s. 2].  

---  
Zdôvodnenie:  
- V úryvku na strane 2 je uvedené, že najznámejšie francúzske dezerty zahŕňajú Creme brulée, Palacinka, Makronky, Mousse, Opera, Paris–Brest a Profiteroly.  
- Tieto názvy sú priamo uvedené v dokumente ako príklady najznámejších francúzskeho dezerty.  
- Nie je tu žiadne zmysluplné odvodenie alebo vyhodnocovanie, ktoré by nepresne identifikovalo tieto produkty ako "najznámejšie".


## 12. [dokumenty] Ako sa pripravuje piškótový korpus?

- pojmy z ontológie: —
- nájdené zdroje: sk_SPPK_francuzske_dezerty.pdf s.3 (0.03); sk_SPPK_francuzske_dezerty.pdf s.4 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03)
- čas: 254 s

Pripravenie piškotového korpuza zahŕňa nasledujúce kroky: bielky a dve tretiny cukru sa vyšľahávajú na tuhý sneh, žĺtky a jedna tretina cukru sa vymiešavajú s vodou; obidva peny sa zľahka spojíme. Pridáme preosiatu múku so citrónovou kôrou, rozotrieme na plech pokrytý papierom veľkosť 30x40cm a plát upečieme pri teplote 200 °C po dobu 7–10 minút [sk_SPPK_francuzske_dezerty.pdf, s. 4].

---  
Zdôvodnenie:  
- V úryvku je popis postupu pripravy piškotového korpuza so zložením (bielky, cukor, žĺtky, voda, múka, citrónova kôra).  
- Uvedený postup sa týka konkrétneho prípravu piškotového korpuza ako zloženia a techniky.  
- V kontexte nie je uvedená žiadna iná metóda alebo alternatívny spôsob pripravy, preto odpoveď sa zameriava len na popis v dokumente [sk_SPPK_francuzske_dezerty.pdf, s. 4].


## 13. [recepty] Ako sa pripravuje Sacherova torta a aká glazúra sa na ňu používa?

- pojmy z ontológie: Cake
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.7 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.7 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03)
- čas: 273 s

V dostupných dokumentoch to nie je uvedené.  

---  
Zdôvodnenie:  
- V úryvku [sk_Sladke_recepty_zo_Slovenska.pdf, s. 7] sa zvyšuje len informácia o tom, že Sacherova torta bola vylepšená čokoládovou polevou a marhuľovou marmeládou, ale nie je uvedené, ako sa pripravuje ani aká glazúra sa na ňu používa.  
- Nemenovaný výrobok "Sacher torta" z dokumentu [sk_Luigi_Dolci_katalog_2026.pdf] má glazúru z tmavej čokolády, ale nie je jasne uvedené, že sa jedná o Sacherovu tortu.  
- Žiadna informácia v dokumentoch neuvádza presné kroky pripravenia a konkrétnej glazúry pre Sacherovu tortu.


## 14. [recepty] Ako sa pečú vanilkové rožky?

- pojmy z ontológie: Croissant, Vanilla
- nájdené zdroje: sk_Sladke_recepty_zo_Slovenska.pdf s.11 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.12 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.12 (0.03); sk_Zmrzlina.pdf s.3 (0.03)
- čas: 299 s

Vanilkové rožky sa pečú tak, že na doske zhnete všetky suroviny do cesty a necháte ich odležať v chlade. Zo studeného cesta tvarujete rožky a pečiete vo vyhriatej rúre pri 220 °C 8 až 10 minút [sk_Sladke_recepty_zo_Slovenska.pdf, s. 11]. Po vybratí z rúry rožky obaľujete vo vanilko vom cukre.

---  
Zdôvodnenie:  
- V úryvku sa uvádzajú kroky pečenia vanilkových rožkov [sk_Sladke_recepty_zo_Slovenska.pdf, s. 11].  
- Uvedené suroviny (múka, cukor, maslo, vlašské orechy) sa zhnete do cesty a tvarujete rožky [sk_Sladke_recepty_zo_Slovenska.pdf, s. 11].  
- Pečenie prebieha vo vyhriatej rúre pri teplote 220 °C po dobu 8–10 minút [sk_Sladke_recepty_zo_Slovenska.pdf, s. 11].  
- Po pečení sa rožky obaľujú vo vanilko vom cukre [sk_Sladke_recepty_zo_Slovenska.pdf, s. 11].


## 15. [odbor cukrár] Aké hygienické zásady musí dodržiavať cukrár pri práci?

- pojmy z ontológie: PastryChef
- nájdené zdroje: sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.4 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.65 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.26 (0.03); sk_SPPK_zaverecna_skuska_cukrar_2025.pdf s.18 (0.03)
- čas: 370 s

Hygienické zásady, ktoré musí dodržiavať cukrár pri práci, zahŕňajú správne zachovanie hygény v prevádzke pri práci s potravinami a realizáciu sanitácii vo výrobe [sk_SPPK_zaverecna_skuska_cukrar_2025.pdf, s. 65].  

---  
Zdôvodnenie:  
- V dokumente je uvedené, že musí sa zameriavať na hygienické zásady pri práci s potravinami [sk_SPPK_zaverecna_skuska_cukrar_2025.pdf, s. 65].  
- Je tiež spomenutá sanitácia ako dôležitý príklad opatrenia vo výrobe cukrárskeho výrobku [sk_SPPK_zaverecna_skuska_cukrar_2025.pdf, s. 65].  
- Hygiena a sanitácia sa zvyšuje ako samostatný okruh skúšky, čo ukazuje ich dôležitosť v praxi cukrárskej práce.


## 16. [zloženie] Z čoho sa skladá čokoládová plnka a aké alergény obsahuje?

- pojmy z ontológie: Chocolate
- nájdené zdroje: sk_iCukraren_zlozenie_a_alergeny.pdf s.1 (0.03); sk_SPPK_cokolada_temperovanie_pralinky.pdf s.5 (0.03); sk_SPPK_ganache.pdf s.3 (0.03); sk_Cokolada.pdf s.3 (0.03)
- čas: 505 s

Čokoládová plnka sa sklada z mascarpone, šlahačky a cukru a pravé belgické čokolády Callebaut (kakaová masa; cukor; kakao s nízkym obsahom tuku; emugátor: sójový lecitín; aróma: prírodná vanilka). Obsahuje alergény mlieko a orechy.  

---  
Zdôvodnenie:  
- Z tabuľky alerógénov je uvedené, že čokoládová plnka má zloženie s mascarpone, šlahačkou, cukrom a pravou belgickou čokoládou Callebaut [sk_iCukraren_zlozenie_a_alergeny.pdf, s. 1].  
- V stĺpci ALERGÉNY je uvedené, že obsahuje mlieko (a orechy pri pridaní čokolády) – v zložení sa nachádza sójový lecitín a vanilka; alergény sú určité len podľa tabuľky [sk_iCukraren_zlozenie_a_alergeny.pdf, s. 1].  
- Vanilka nie je alergénom (podľa pravidla), ale sójový lecitín môže byť alergénom – v zozname sa to neuvádza ako osobný alerógén; preto sa uvádzajú len uvedené alergény [sk_iCukraren_zlozenie_a_alergeny.pdf, s. 1].  
- V prípade č


## 17. [katalóg] Aké cheesecaky ponúka Luigi Dolci?

- pojmy z ontológie: —
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03)
- čas: 103 s

V dostupných dokumentoch to nie je uvedené.


## 18. [katalóg] Na koľko porcií je torta od Luigi Dolci a ako dlho vydrží zmrazená?

- pojmy z ontológie: Cake
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03)
- čas: 270 s

Torta od Luigi Dolci je na 12 porcií a vydrží zmrazená 12 mesiacov.  

---  
Zdôvodnenie:  
- V dokumente [sk_Luigi_Dolci_katalog_2026.pdf, s. 2] sa uvádzajú "každá torta je predkrájaná na 12 rovnakých porcií".  
- Toto tvrdenie potvrdzuje, že každá torta má presne 12 porcí.  
- V tej istej sekcie sa uvádzajú: "Pri −18 °C vydržia torty a cheesecaky 12 mesiacov od výroby", čo znamená, že zmrazené torty vydržia 12 mesiacov.


## 19. [katalóg + ontológia] Ktoré produkty obsahujú tiramisu a mascarpone?

- pojmy z ontológie: Tiramisu, Product, Mascarpone
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03); sk_iCukraren_zlozenie_a_alergeny.pdf s.1 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.5 (0.03); sk_Zmrzlina.pdf s.3 (0.03)
- čas: 488 s

Produkty, ktoré obsahujú tiramisu a mascarpone, sú: Tiramisu pohár [sk_Luigi_Dolci_katalog_2026.pdf, s. 5] a Cheesecake Nocciola (zoznam výrobkov z dokumentu) – ale podľa ontológie je cheescake niekde uvedený ako produkt so surovinami [sk_iCukraren_zlozenie_a_alergeny.pdf, s. 1], ktoré obsahujú mascarpone a vajcia.

Zdôvodnenie:  
- Tiramisu pohár je explicitne uvedený ako produkt so zložením „čokoládový piškót s espressom, nadýchaný krém tiramisu“ [sk_Luigi_Dolci_katalog_2026.pdf, s. 5], a podľa ontológie má tiramisu ako výrobok ingredient mascarpone (tiramisu hasIngredient Mascarpone).  
- Cheesecake Nocciola je uvedený vo zozname produktov [sk_Luigi_Dolci_katalog_2026.pdf, s. 5] a podľa zloženia v dokumente „Zmrzlina“ (alebo iných) nie je priamo pomenované ako obsahujúce tiramisu; preto sa nepodarí dokázať jeho prítomnosť vo vzácnej kategórii.  
- V zložení „Orechová mascarpone“ a „Čokoládová mascarpone“ je uvedené, že obsahujú mascarpone [


## 20. [mimo domény] Koľko stojí pizza margherita?

- pojmy z ontológie: —
- nájdené zdroje: sk_Luigi_Dolci_katalog_2026.pdf s.2 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.3 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.13 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.8 (0.03)
- čas: 466 s

Tento produkt v ponuke našej cukrárne nie je.  

---  
Zdôvodnenie:  
- V kontexte sa nepomínajú žiadne produkty, ktoré by boli pizami alebo "pizza margherita".  
- Ceny a produkty z ontológie obsahujú iba tiramisu, cheesecake, čokoládovu tortu a kávu.  
- V dokumentoch sa nepomínajú žiadne informácie o pizách alebo podobných výrobkoch.


## 21. [cena – nie je v ponuke] Koľko stojí Sacherova torta?

- pojmy z ontológie: Cake
- nájdené zdroje: sk_Sladke_recepty_zo_Slovenska.pdf s.7 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.7 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.4 (0.03)
- čas: 297 s

V dostupných dokumentoch to nie je uvedené.  

---  
Zdôvodnenie:  
- V úryvku [sk_Sladke_recepty_zo_Slovenska.pdf, s. 7] sa Sacherova torta spomína ako základný výrobok, ale nie je uvedené jej zoznam surovín ani cena.  
- V úryvku [sk_Luigi_Dolci_katalog_2026.pdf, s. 4] sa Sacher torta objavuje ako produkt (12 porcií), avšak bez ceny a bez uvedenia v ponuke naše cukrárne.  
- V ontológii nie je žiadny záznam o "Sacherova torte" ani jej cene, čo znamená, že toto tvrdenie nepripadá do kategórie produktov našej cukrárne.


## 22. [alergény] Aké alergény má orechová plnka?

- pojmy z ontológie: Nuts
- nájdené zdroje: sk_iCukraren_zlozenie_a_alergeny.pdf s.1 (0.03); sk_Sladke_recepty_zo_Slovenska.pdf s.23 (0.03); sk_Luigi_Dolci_katalog_2026.pdf s.6 (0.03); sk_iCukraren_zlozenie_a_alergeny.pdf s.1 (0.03)
- čas: 257 s

Alergény orechovej plnke sú mlieko a orechy.  

---  
Zdôvodnenie:  
- V tabuľke alerógénov [sk_iCukraren_zlozenie_a_alergeny.pdf, s. 1] je uvedené, že orechová plnka má alergény: mlieko, orechy.  
- Tento fakt je priamo zaznamenaný v stĺpci ALERGÉNY pre "Orechová plnka".
