# crawling task
craling task uzduotis ( individuali)


** Apie programa

Programa perskaito 4 NŠA puslapius , atsiunčia VBE ir PUPP užduočių PDF bei vertinimo instrukcijas, kiekvienam failui nustatomi metadata, susieja kiekvieną užd. su vertinimo instrukcija ir sukuria JSON indeksa.


** paleidimas
paleisti programa reikia python ir bibliotekų
Bibliotekoms įrašyti į terminala reikia parašyti:

pip install -r requirements.txt

Ir tuomet paleisti pačią programą terminale:

python crawl.py


** Ką atlieka programa:

Paleidus programą yra atsiunčiami PDF failai iš NŠA (apie 1,1GB), tai gali užtrukti tad reiks palaukti (vizualaus siuntimo lango nedariau). Jau atsiųsti failai nesiunčiami iš naujo ir jei bus nutrauktas paleidimas ir pradėtas naujai siųsti jis siųs nuo paskutinio atsiųsto failo toliau.

Programa klaidos atveju darbo nenutraukia t.y. bloga pdf nuoroda, faila, kurio neina įrašyti ar kitokia bloga nuoroda yra įrašoma į log(žurnala) ir tesia darbą toliau. Taip pat programa bando nuskaityti puslapi kelis kartus ir jei nepavyksta po 3 bandymų programa sustoja su klaidos kodu 1 ir nepakeičia /index.json 


