from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .config import OUT_OF_SCOPE_HOST
from .context import skaityt_kontekst
from .metadata import fold, rast_sesija, rast_egzaminotip, rast_dali, rast_srauta, rast_lygi

def metai(a):
    skyr= a.find_parent(class_="panel")
    if skyr is None:
        return None
    title = skyr.select_one(".panel-heading").get_text(strip=True)
    return int(title) if title.isdigit() else None

def surinkt(family, page_tipas, page_url, html):
    docs = []
    for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
        url = urljoin(page_url, a["href"].strip())
        if OUT_OF_SCOPE_HOST in url:
            continue
        if not url.lower().endswith(".pdf"):
            continue
        text = a.get_text(" ", strip=True)
        f = fold(text)
        ctx = skaityt_kontekst(a, url)
        docs.append({"role": page_tipas, "family": family, "url": url, "text": text, "year": metai(a),
                     "sesija": rast_sesija(f), "egzaminotip": rast_egzaminotip(f), "dalis": rast_dali(f), "srautas": rast_srauta(f),
                     "lygis": rast_lygi(f), "in_table": ctx["in_table"], "row": ctx["row"], "column": ctx["column"]})
        
    return docs