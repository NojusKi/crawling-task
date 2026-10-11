import requests

from .config import PAGES, PDF_DIR
from .pages import surinkt
from .storage import download

def gaut_psl(url):
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    return response.content.decode("utf-8")

def kiek (docs, laukas):
    return sum(1 for d in docs if d[laukas])

def main():
    for family, page_tipas, page_url in PAGES:
        docs, praleista = surinkt(family, page_tipas, page_url, gaut_psl(page_url))
        print(family, page_tipas, len(docs), "PDF | užduočių:", sum(1 for d in docs if d["role"] == "task"),
              "| raktų:", sum(1 for d in docs if d["role"] == "key"), "| priedų:", sum(len(d["attachments"]) for d in docs))
        for priezastis, kiekis in praleista.most_common():
            print("   praleista", kiekis, "-", priezastis)
        print("  rasta: metai", kiek(docs, "year"), "| dalykas", kiek(docs, "dalykas"), "|dalis", kiek(docs, "dalis"),
              "| srautas", kiek(docs, "srautas"), "| lygis", kiek(docs, "lygis"))
        print("  rūšis", kiek(docs, "rusis"), "| darbo dalis", kiek(docs, "darbo_dalis"),
              "| pakartotinė sesija", sum(1 for d in docs if d["sesija"] == "pakartotinė"),
              "| be sesijos", sum(1 for d in docs if d["sesija"] is None))
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