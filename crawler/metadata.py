import re
import unicodedata

LKL ="Lietuvių kalba ir literatūra"

def fold(tekstas): # mazosios raides, be diakritiniu zenklu
    tekstas = unicodedata.normalize("NFKD", tekstas.lower())
    isvalytas_tekst = "".join(simbolis for simbolis in tekstas if not unicodedata.combining(simbolis))
    return re.sub(r"\s+", " ", isvalytas_tekst).strip()

def rast_sesija(f):
    if "pakartotin" in f:
        return "pakartotinė"
    if re.search(r"pagrindin\w* sesij", f):
        return "pagrindinė"
    return None

def rast_egzaminotip(f):  # valstybinis ar mokyklinis 
    mokykla = re.search(r"mokyklin|\bmbe\b", f)
    tipas = re.search(r"valstybin(is|io|iu|iai)\b|\bvbe\b",f)
    if mokykla and not tipas:
        return 'mokyklinis'
    if tipas and not mokykla:
        return "valstybinis"
    return None

def rast_dali(f): # egzamino dalys
    m = re.search(r"\b(iii|ii|i)\s+(?:vbe\s+)?dal(is|ies|yje|iai|i)\b", f)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(pirm|antr|trec)\w*\s+dal",f) # antr dalis
    if m:
        return {"pirm": "I", "antr": "II", "trec": "III"}[m.group(1)]
    return None

def rast_srauta(f):
    m = re.search(r"\b(iii|ii|i)[\s-]*sraut", f)
    if m:
        return m.group(1).upper()
    return None

def rast_lygi(f):
    if re.search(r"\bbendr(asis|ojo|ojoje|osios)\b|matematik\w*\s*\(b\)", f):
        return "bendrasis"
    if re.search(r"isplestin|matematik\w*\s*\(a\)",f):
        return "išplėstinis"
    return None

# regex, dalykas. laimi pirm atitikimas pagal tvarka
DALYKAI = [
    ("daile ir muzik", "Dailė ir muzika"), ("muzikolog|muzikos istorij|mastymo", "Muzikologija"),
    ("muzik", "Muzika"), ("daile", "Dailė"), ("matematik", "Matematika"), ("biolog", "Biologija"),
    ("chemij", "Chemija"), ("fizik", "Fizika"), ("istorij", "Istorija"), ("geograf", "Geografija"),
    ("filosof", "Filosofija"), ("ekonomik", "Ekonomika ir verslumas"), ("informacin", "Informacinės technologijos"),
    ("informatik", "Informatika"), ("inzinerin|inzinier", "Inžinerinės technologijos"), ("gamtos mokslai", "Gamtos mokslai"),
    ("socialiniai mokslai", "Socialiniai mokslai"), ("tikyb", "Tikyba"),
]
INZINERIJOS_SRITYS = {"strukturin": "struktūrinės sistemos ir statiniai", "mechanin": "mechaninės sistemos ir transportas",
                      "elektronik": "elektronika", "robotik": "robotika ir mechatronika", "aplink": "aplinka ir energetika"}
KALBOS = {"angl": "anglų", "pranc": "prancūzų", "rus": "rusų", "vokiec": "vokiečių",
          "lenk": "lenkų", "baltarus": "baltarusių", "lietuv": "lietuvių"}


# atskiros egzamino dalys turi atskirus darbus
DARBO_DALYS = [
    ("kurybin|bilietai", "kūrybinė"), ("diktant|natos", "diktantas"), ("muzikos istorij", "muzikos istorija"),
    ("mastymo", "mąstymas"), ("suvokim", "suvokimas"), ("interpretacij", "interpretacija"),
    ("rasym|rasin|teksto kurim", "rašymas"), ("kalbejim|zodziu", "kalbėjimas"),
    ("klausym", "klausymas"), (r"\btest(as|ai|o)\b", "testas"),
]

RUSYS = [
    ("bandom", "bandomoji"), ("pavyzd", "pavyzdinė"), ("kurtiesiems|kurciuj|neprigirdin", "kurtiesiems"),
    ("tarpin", "tarpinis"),
]

def rast_dalyka(f, pupp=False): # ar tai PUPP puslapis
    for sablonas, dalykas in DALYKAI:
        if re.search(sablonas, f):
            if dalykas.startswith("Inž"): # turi 5 sritis
                dalykas += next((f" ({sritis})" for k, sritis in INZINERIJOS_SRITYS.items() if k in f), "")
            return dalykas
    
    kalbos = {KALBOS[m] for m in re.findall(r"\b(" + "|".join(KALBOS) +")", f)}
    if len(kalbos) != 1:
        return None # arba kalbos nera arba ju kelios tai dalyko nenustatom
    kalba = kalbos.pop()
    gimtoji= re.search(r"gimt[oa]|tautines", f) or kalba in ("lenkų", "baltarusių")
    if pupp and "uzsienio" not in f and kalba != "lietuvių":
        gimtoji = True 
    if gimtoji:
        return "Lietuvių kalba (gimtoji)" if kalba == "lietuvių" else f"Gimtoji kalba ({kalba})"
    if kalba == "lietuvių":
        return "Lietuvių kalba (valstybinė)" if "valstybine" in f and "literat" not in f else LKL 
    return f"Užsienio kalba ({kalba})"

def rasti_rusi(f):
    for sablonas, rusis in RUSYS:
        if re.search(sablonas, f):
            return rusis
    return None

def rast_darbo_dali(f):
    for sablonas, dalis in DARBO_DALYS:
        if re.search(sablonas, f):
            return dalis
    return None

""" 
apie VIETOS .

kuriuose tekst ieskoti kiekvieno lauko
own - tai pacios nuorodos tekstas, lenteles eil, stulp antrastes, lent pavadinimas.
file - tai PDF failo vards
near - artimiausia antraste virs nuorodos
all - vosos antrastes virs nuorodos
"""

VIETOS = {
    "dalykas": ("own", "near"),
    "egzaminotip": ("own", "file", "near"),
    "sesija": ("own", "file", "all"),
    "srautas": ("own", "file", "near"),
    "dalis": ("own", "file", "all"),
    "lygis": ("own", "file", "near"),
    "rusis": ("own", "file", "near"),
    "darbo_dalis": ("own", "file", "near"),
}

SKAITYTOJAI = {
    "egzaminotip": rast_egzaminotip, "sesija": rast_sesija, "srautas": rast_srauta,
    "dalis": rast_dali, "lygis": rast_lygi, "rusis": rasti_rusi, "darbo_dalis": rast_darbo_dali,
}

def pirma_rasta(tekstai, skaitytojas):
    for tekstas in tekstai:
        reiskme = skaitytojas(fold(tekstas))
        if reiskme:
            return reiskme
    return None

def skaityt_metaduomenis(ctx, role, family): # visi laukai kartu
    vietos = {
        "own": [ctx["label"], ctx["row"], ctx["column"], ctx["title"]],
        "file": [ctx["file_name"]],
        "near": ctx["headings"][:1], # pirma, artimiausia antraste
        "all": ctx["headings"],
    }
    meta = {}
    for laukas, kur in VIETOS.items():
        tekstai= []
        for vieta in kur:
            tekstai += vietos[vieta] # susjungia srities tekstus i viena sarasa
        if laukas == "dalykas":
            skaitytojas = lambda f: rast_dalyka(f, pupp=family == "PUPP")
        else:
            skaitytojas = SKAITYTOJAI[laukas]
        meta[laukas] = pirma_rasta(tekstai,skaitytojas)
    
    if meta["rusis"] in ("bandomoji", "pavyzdinė"):
        meta["sesija"] = pirma_rasta(vietos["own"], rast_sesija) # band/ pavyzdin darbai nepriklauso
    elif meta["sesija"] is None and not (role == "key" and meta["dalykas"] == LKL):
        meta["sesija"] = "pagrindinė" # sesija nenurodyta 
    meta["egzaminotip"] = meta["egzaminotip"] or "valstybinis"
    return meta