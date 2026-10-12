import requests
import re
import hashlib
from urllib.parse import unquote, urlparse
from .config import PDF_DIR
from .metadata import fold
import os
import time
from pathlib import Path


MAX_META_SIMBOLIU = 140
ILGO_KELIO_PREFIKS = "\\\\?\\" # ilgiems path nustatyti

def slug(tekstas):
    return re.sub(r"[^a-z0-9]+", "-", fold(tekstas or "")).strip("-")

def failo_kelias(doc, url, priedas=False): # kur bus PDF
    meta= [doc["year"], doc["family"], doc["egzaminotip"], slug(doc["sesija"]), slug(doc["dalykas"]), slug(doc["lygis"]),
    doc["srautas"] and f"srautas-{doc['srautas']}", doc["dalis"] and f"dalis-{doc['dalis']}",
    slug(doc["rusis"]), slug(doc["darbo_dalis"]), priedas and "priedas"]
    meta_dalis = "_".join(str(m) for m in meta if m)[:MAX_META_SIMBOLIU]
    orginalus = re.sub(r"[^A-Za-z0-9._-]+", "_", unquote(urlparse(url).path.rsplit("/", 1)[-1]))[-60:]
    aplankas = PDF_DIR/ doc["family"] / str(doc["year"]) / ("vertinimo_instrukcijos" if doc["role"] =="key" else "uzduotys")
    return aplankas / f"{meta_dalis}__{orginalus}"

def planuoti_route(uzduotys, raktai): # url kelias
    keliai = {}
    uzimti = {} # del sutapimu
    for doc in uzduotys + raktai:
        failai = [(doc["url"], False)] + [(url, True) for url in doc["attachments"]] # pati uzd/raktas
        for url, priedas in failai:
            if url in keliai:
                continue
            kelias = failo_kelias(doc, url, priedas)
            if uzimti.get(kelias, url) != url:
                kelias = kelias.with_name(f"{kelias.stem}-{hashlib.md5(url.encode()).hexdigest()[:6]}.pdf")
            keliai[url] = kelias
            uzimti[kelias] = url
    return keliai

def disko_kelias(kelias):
    return Path(ILGO_KELIO_PREFIKS + os.path.abspath(kelias)) if os.name == "nt" else kelias

def pilnas_dydis(r):
    if r.headers.get("Content-Encoding"):
        return None # suspaudziamas turinys
    if r.status_code == 206:
        return int(r.headers["Content-Range"].rsplit("/", 1)[-1])
    return int(r.headers.get("Content-Length") or 0) or None

def download(url, destination):
    diske = disko_kelias(destination)
    try:
        if diske.exists():
            with open(diske, "rb") as f:
                if b"%PDF-" in f.read(1024):
                    return True, ""
    except OSError:
        pass
    dalinis = diske.with_name(diske.name + ".part")
    klaida = ""
    for bandymas in range(5):
        time.sleep(0.3)
        try:
            turim = dalinis.stat().st_size if dalinis.exists() else 0
            with requests.get(url, headers={"Range": f"bytes={turim}-"} if turim else {}, timeout=40, stream=True) as r:
                if r.status_code >= 500:
                    klaida = f"HTTP {r.status_code}"
                    time.sleep(2*(bandymas + 1))
                    continue
                if r.status_code == 416:
                    dalinis.unlink()
                    continue
                if r.status_code not in (200, 206):
                    return False, f"HTTP {r.status_code}"# jei gaunam 404 nekartoti
                if r.status_code == 200:
                    turim = 0
                laukiamas = pilnas_dydis(r)
                diske.parent.mkdir(parents=True, exist_ok=True)
                with open(dalinis, "ab" if turim else "wb") as f:
                    for dalis in r.iter_content(1 << 16):
                        f.write(dalis)
            dydis = dalinis.stat().st_size
            if laukiamas and dydis != laukiamas:
                raise IOError(f"nepilnas failas {dydis} is {laukiamas} baitu")
            with open(dalinis, "rb") as f:
                yra_pdf = b"%PDF-" in f.read(1024)
            if not yra_pdf:
                dalinis.unlink()
                return False, "ne PDF failas"
            
            os.replace(dalinis, diske)
            return True, ""
        except Exception as e:
            klaida = f"{type(e).__name__}: {e}"
            time.sleep(2 * (bandymas + 1))
    return False, klaida
            