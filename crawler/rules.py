import re
from .metadata import fold, rast_dalyka

#sablonai lyginami su fold tekstu, mazom raidem ir be diakritiku
PRIEDAS = re.compile(r"^\(?\s*pried(as|ai)\b") # pvz formuliu lapas
ATSAKYMU_LAPO_STULPELIS = re.compile(r"atsakymu lap|islaikymo|klausymo|failo pavadinimas") # islaikymo riba, garso irasai, failu sarasas
NE_UZDUOCIU_LENTELE = re.compile(r"atsakymu lap|mokiniu .*pavyzdz|mokiniu darb|kokybine analiz|rezultat|kriterij")
NE_UZDUOTIS = re.compile (r"potem|kriterij|analiz|komentar|specifikacij|aptart|vertinim|tyrim|rezultat|instrukcij|lentel")
ATRODO_KAIP_UZDUOTIS = re.compile(r"uzduot|testas|rasinys|rasymo|temos ir klausimai")
NE_RAKTAS = re.compile(r"pavyzdz|analiz|tyrim|rezultat|potem|mokymu|kriterij|vertinimo lap|gair|slenksti|uzdaviniu")

TASK, KEY, ATTACH = "task", "key", "attachment"

def klasifikuot(ctx, page_tipas, family):
    label=fold(ctx["label"])
    # formuliu lapas (priedas)
    if page_tipas == TASK and PRIEDAS.match(fold(ctx["link_text"])):
        return ATTACH, ""
    
    metu_skyrius = bool(re.fullmatch(r"(19|20)\d\d", ctx["section"]))
    if ctx["section"] and not metu_skyrius and not (page_tipas == KEY and "vertinimo instrukcij" in label):
        return None, "vertinimo medžiaga (mokym skaidrės, kriterijai)"
    
    role = page_tipas
    if ctx["in_table"]:
        if ctx["in_subject_column"]:
            return None, "pagalbinis dokumentas dalyko stulpelyje"
        if page_tipas == TASK:
            if ATSAKYMU_LAPO_STULPELIS.search(fold(ctx["column"])):
                return None, "atsakymų lapo / išlaikymo ribos / garso stulpelis"
            artimiausia = ctx["headings"][0] if ctx["headings"] else ""
            if NE_UZDUOCIU_LENTELE.search(fold(ctx["title"] + " " + artimiausia)):
                return None, "atsakymų lapų, kriterijų, analizių ar mokinių darbų lentelė"
            if "vertinimo instrukcij" in fold(ctx["column"]):
                role = KEY
    elif page_tipas == TASK:
        if NE_UZDUOTIS.search(label) or not ATRODO_KAIP_UZDUOTIS.search(label) or not rast_dalyka(label, pupp=family == "PUPP"):
            return None, "pavienė nuoroda, kuri nėra užduotis"
        
    if role == TASK and "vertinim" in label:
        if "instrukcij" not in label:
            return None, "vertinimo kriterijai prie užduočių"
        role = KEY
    if role == KEY and NE_RAKTAS.search(label):
        return None, "rubrika/ kriterijai/ analizė tarp instrukcijų"
    return role, ""
            