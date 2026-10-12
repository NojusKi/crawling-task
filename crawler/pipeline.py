import json
import logging
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from .config import INDEX_FILE, LOG_FILE, OUT_DIR, PAGES
from .matching import rasti_rakta
from .pages import surinkt
from .storage import planuoti_route, download

RASTA, NERA, NEVEIKIA = "found", "missing", "broken_link"

def gaut_psl(url, bandymai=3): # keliu kartu bandymas
    for bandymas in range(bandymai):
        try:
            response =requests.get(url, timeout=40)
            response.raise_for_status()
            return response.content.decode("utf-8")
        except Exception:
            if bandymas == bandymai -1:
                raise
            time.sleep(3* (bandymas + 1))
            
ATSPAUDO_LAUK= ("role", "family", "url", "year", "dalykas", "egzaminotip", "sesija", "srautas", "dalis", "lygis", "rusis", "darbo_dalis")

def atspaudas(doc):
    return tuple(doc[k] for k in ATSPAUDO_LAUK) + tuple(doc["attachments"])

def visi_dokumentai():
    docs  = []
    nepavyke = []
    for family, page_tipas, page_url, in PAGES:
        try:
            rasta, praleista = surinkt(family, page_tipas, page_url, gaut_psl(page_url))
        except Exception as e:
            logging.error("nepavyko perskaityti psl %s: %s", page_url, e)
            nepavyke.append(page_url)
            continue
        logging.info("%s %s puslapis: %d PDF, praleista: %s", family, page_tipas, len(rasta), dict(praleista) or "-")
        docs += rasta
        
    unikalus, matyta = [], set()
    for doc in docs:
        if atspaudas(doc) not in matyta:
            matyta.add(atspaudas(doc))
            unikalus.append(doc)
    for doc in unikalus:
        if not doc["dalykas"] or not doc["year"]:
            logging.warning("nerastas dalykas arba metai, susiet nepaeis: %s", doc["url"])
            
    uzduotys, uzd_adresai = [], set()
    for doc in unikalus:
        if doc["role"] == "task":
            if doc["url"] in uzd_adresai:
                logging.info("ta pati uzduotis pakartotinai isvardinta du kartus (%s), paliekama viena eilute: %s", doc["year"], doc["url"])
                continue
            uzd_adresai.add(doc["url"])
            uzduotys.append(doc)
    return uzduotys, [d for d in unikalus if d["role"] == "key"], nepavyke

def atsisiuti_viska(keliai):
    rezultatai= {}
    with ThreadPoolExecutor(3) as pool:
        for url, rezultatas in zip(keliai, pool.map(lambda url: download(url, keliai[url]), keliai)):
            rezultatai[url] = rezultatas
            if len(rezultatai) % 100 == 0:
                logging.info("atsiusta %d is %d", len(rezultatai), len(keliai))
    return rezultatai

def sudaryti_eilutes(uzduotys, rakto_nuorodos, keliai, atsiusta):
    kelias= lambda url: keliai[url].as_posix()# kelias su pasvirusiais bruksniais
    eilutes = []
    for uzd, raktas in zip(uzduotys, rakto_nuorodos):
        uzd_ok, uzd_klaida = atsiusta[uzd["url"]]
        rak_ok, rak_klaida = atsiusta[raktas["url"]] if raktas else (False, "")
        
        if not uzd_ok:
            statusas = NEVEIKIA
            logging.warning("neveikianti uzd nuorodoa(%s): %s", uzd_klaida, uzd["url"])
        elif raktas and not rak_ok:
            statusas = NEVEIKIA
            logging.warning("neveikia vertinimo istrukcijos nuoroda (%s): %s", rak_klaida, raktas["url"])
        elif raktas:
            statusas = RASTA
        else:
            statusas = NERA
            logging.debug("nera vertinimo instrukcijos: %s %s %s %s", uzd["year"], uzd["dalykas"], uzd["sesija"], uzd["url"])
        for url in uzd["attachments"]:
            if not atsiusta[url][0]:
                logging.warning("neveikia priedo (formul. lapo) nuoroda (%s): %s", atsiusta[url][1], url)
                
        eilutes.append({
            "year": uzd["year"], "subject": uzd["dalykas"], "exam_type": uzd["egzaminotip"], "session": uzd["sesija"],
            "srautas": uzd["srautas"], "dalis": uzd["dalis"], "level": uzd["lygis"], "task_file_path": kelias(uzd["url"]) if uzd_ok else None,
            "answer_file_path": kelias(raktas["url"]) if raktas and rak_ok else None,
            "source_url": uzd["url"], "status": statusas, "family": uzd["family"], 'variant': ", ".join(x for x in (uzd["rusis"], uzd["darbo_dalis"]) if x) or None,
            "attachments_file_path": [kelias(u) for u in uzd["attachments"] if atsiusta[u][0]], 
        })
    eilutes.sort(key=lambda e: (e["family"], -(e["year"] or 0), e["subject"] or "", e["session"] or "", e["source_url"]))
    return eilutes

def raktai_be_uzduociu(raktai, rakto_nuorodos, atsisiusta):
    susieti = {r["url"] for r in rakto_nuorodos if r}
    for raktas in raktai:
        if raktas["url"] not in susieti:
            ok, klaida = atsisiusta[raktas["url"]]
            logging.log(logging.DEBUG if ok else logging.WARNING, "vertinimo instrukcij be uzduoties PDF%s: %s %s %s",
                        ""if ok else f" (NEVEIKIA, {klaida})", raktas["year"], raktas["dalykas"], raktas["url"])

def main():
    OUT_DIR.mkdir(exist_ok=True)
    failas = logging.FileHandler(LOG_FILE, "w", encoding="utf-8") # raso i faila viska
    ekranas = logging.StreamHandler()
    ekranas.setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s", handlers=[failas, ekranas])
    logging.getLogger("urllib3").setLevel(logging.WARNING)   
    uzduotys, raktai, nepavyke_psl = visi_dokumentai()
    if nepavyke_psl or not uzduotys:
        logging.error("Neperskaityti psl.: %d iš %d, indeksas paliekamas", len(nepavyke_psl), len(PAGES))
        return 1
    rakto_nuorodos = [rasti_rakta(u, raktai) for u in uzduotys]
    keliai = planuoti_route(uzduotys, raktai)
    logging.info("%d uzduociu, %d vertinimo istrukciju, %d failu atsisiuti", len(uzduotys), len(raktai), len(keliai))
    atsisiusta = atsisiuti_viska(keliai)
    
    eilutes = sudaryti_eilutes(uzduotys, rakto_nuorodos, keliai, atsisiusta)
    INDEX_FILE.write_text(json.dumps(eilutes, ensure_ascii=False, indent=2), encoding="utf-8")
    raktai_be_uzduociu(raktai, rakto_nuorodos, atsisiusta)
    logging.info("baigta: %d eilutės %s", len(eilutes), {s: sum(e["status"] == s for e in eilutes) for s in (RASTA, NERA, NEVEIKIA)})
    return 0