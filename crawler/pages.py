from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import Counter
from .config import OUT_OF_SCOPE_HOST
from .context import skaityt_kontekst
from .metadata import skaityt_metaduomenis
from .rules import ATTACH, klasifikuot

def surinkt(family, page_tipas, page_url, html):
    docs = []
    praleista = Counter() # nuorodu praleidimui
    uzd_langelyje = {}
    for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
        url = urljoin(page_url, a["href"].strip())
        if OUT_OF_SCOPE_HOST in url:
            praleista["etestavimas.lt"] += 1
            continue
        if not urlparse(url).path.lower().endswith(".pdf"): # patikrint adresa
            continue
        ctx = skaityt_kontekst(a, url)
        role, priezastis = klasifikuot(ctx, page_tipas, family)
        langelis = id(a.find_parent("td")) # atpazinimo zenklas
        if role is None:
            praleista[priezastis] += 1
        elif role == ATTACH:
            if langelis in uzd_langelyje:
                uzd_langelyje[langelis]["attachments"].append(url) # priedas prie uzduoties
            else:
                praleista["priedas be užduoties"] += 1
        else:
            doc = {"role": role, "family": family, "url": url, "text": ctx["link_text"], "year": ctx["year"],
                   "in_table": ctx["in_table"], "row": ctx["row"], "column": ctx["column"], "attachments": [],
                   **skaityt_metaduomenis(ctx, role, family)}
            docs.append(doc)
            uzd_langelyje[langelis] = doc
            
    return docs,praleista