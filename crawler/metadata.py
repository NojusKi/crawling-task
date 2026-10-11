import re
import unicodedata


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
