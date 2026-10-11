import re
from urllib.parse import urlparse, unquote
from .metadata import fold

INLINE_TAGS = {"strong", "b", "em", "i", "u", "span", "sup", "sub"} # html zymejimai eiluteje, kurie neturi sukelti naujos eilutes

def ar_informatyvus(tekstas):
    be_pdf = re.sub(r"\b(pdf|priedas|priedai|a3|a4)\b", " ", fold(tekstas))
    return bool(re.search(r"[a-z]{3,}", be_pdf))

def tekstas_pries(a):
    dalys = []
    for s in a.previous_siblings:
        vardas= getattr(s, "name", None)
        if vardas is not None and vardas not in INLINE_TAGS: # <br> kita nuorod. ar visas blokas
            break
        dalys.append(s.get_text(" ",) if vardas else str(s))
    return " ".join(reversed(dalys)).strip()

def heading_virs(a, section): # tekstas virs nuorodos, artimiausias pirmas , to paties metu skyriaus
    for s in a.find_all_previous(string=True):
        if section is not None and s.find_parent(class_="panel") is not section:
            return
        if not s.strip() or s.find_parent(["a", "td", "th", "script", "style"]):
            continue
        yield s.strip()
        if section is None and re.match(r"(19|20)\d\d\s*(m\b|metų)", s.strip()):
            return

def rast_metus(pavadinimas, label, headings): #egz metai
    if re.fullmatch(r"(19|20)\d\d", pavadinimas):
        return int(pavadinimas)
    if pavadinimas: # kitokie skyriai
        return max(map(int, re.findall(r"(?:19|20)\d\d", label)), default=None)
    for h in headings: #psl be skyriu
        m = re.match(r"((?:19|20)\d\d)\s*(?:m\b|metu)", fold(h))
        if m:
            return int(m.group(1))
    return None

       
def skaityt_kontekst(a, url): # surenka viska kas apima PDF nuoroda i viena zodyna
    link_text= a.get_text(" ", strip=True)
    section = a.find_parent(class_="panel")
    pavadinimas = section.select_one(".panel-heading").get_text(strip=True) if section is not None else ""
    ctx = {
        "section": pavadinimas,
        "link_text": link_text,
        "label": link_text if ar_informatyvus(link_text) else tekstas_pries(a), # jei nuoroda tik pdf imam teksta pries ja
        "headings": list(heading_virs(a, section)),
        "file_name": re.sub(r"[_\-.]+", " ", unquote(urlparse(url).path.rsplit("/",1)[-1])),
        "in_table": False, "row": "", "column": "", "title": "", "in_subject_column": False,
    }
    ctx["year"] = rast_metus(pavadinimas, ctx["label"], ctx["headings"])
    td= a.find_parent("td")
    if td is not None: # nuorod lenteleje, randama eil ir stulp
        ctx["in_table"] = True
        tr = td.find_parent("tr")
        rows, cells = tr.find_parent("table").find_all("tr"), tr.find_all(["td", "th"])
        header= [] if rows [0].find("a") else rows[0].find_all(["td", "th"]) # pirm eil antraste jei nera linku
        i = cells.index(td) # stulpelis
        if len(header) == 1:
            ctx["title"] = header[0].get_text(" ", strip=True)
        elif i < len(header):
            ctx["column"] = header[i].get_text(" ", strip=True)
            ctx["in_subject_column"] = i == 0 and fold(ctx["column"]) == "dalykas"
        if i > 0 or len(header) > 1:
            eilutes_tekst = " ".join(s for s in cells[0].strings if not s.find_parent("a")) # eil pirm langelis
            ctx["row"] = re.sub(r"\s+", " ", eilutes_tekst).strip()
    return ctx