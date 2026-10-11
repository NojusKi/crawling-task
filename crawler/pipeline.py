import requests

from .config import PAGES, PDF_DIR
from .pages import surinkt
from .storage import download

def gaut_psl(url):
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    return response.content.decode("utf-8")

def main():
    for family, page_tipas, page_url in PAGES:
        docs= surinkt(family, page_tipas, page_url, gaut_psl(page_url))
        print(family, page_tipas, len(docs), "PDF")
        print("  rasta: sesija", sum(1 for d in docs if d["sesija"]), "| tipas", sum(1 for d in docs if d["egzaminotip"]),
              "| dalis", sum(1 for d in docs if d["dalis"]), "| srautas", sum(1 for d in docs if d["srautas"]),
              "| lygis", sum(1 for d in docs if d["lygis"]))
        print("  lentelėje:", sum(1 for d in docs if d["in_table"]), "| su stulpelio antrašte:",
              sum(1 for d in docs if d["column"]), "|su eilutės pavadinimu:", sum(1 for d in docs if d["row"].strip()))
        pavyzdys = next((d for d in docs if d["column"]), None)
        if pavyzdys:
            print("  pavyzdys: eilutė =", pavyzdys["row"].strip()[:40], "| stulpelis=", pavyzdys["column"])
        
        for doc in docs[:5]:
            name = doc["url"].rsplit("/",1)[-1][-60:]
            ok, error = download(doc["url"], PDF_DIR / family / page_tipas / name)
            print("  ", doc["year"], name[:45], "OK" if ok else error)
    return 0