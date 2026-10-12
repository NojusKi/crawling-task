from pathlib import Path

BASE ="https://www.nsa.smsm.lt/pasiekimu-departamentas/egzaminai-ir-pasiekimu-patikrinimai/"

PAGES = [
    ("VBE", "task", BASE + "valstybiniai-brandos-egzaminai/egzaminu-uzduotys/"),
    ("VBE", "key", BASE + "valstybiniai-brandos-egzaminai/vertinimo-instrukcijos/"),
    ("PUPP", "task", BASE + "pagrindinio-ugdymo-pasiekimu-patikrinimai/pupp-uzduotys/"),
    ("PUPP", "key", BASE + "pagrindinio-ugdymo-pasiekimu-patikrinimai/pupp-vertinimo-instrukcijos/")
]

OUT_DIR = Path("duomenys")
PDF_DIR = OUT_DIR / "pdf_failai"
INDEX_FILE = OUT_DIR / "index.json"
LOG_FILE = OUT_DIR / "crawl.log"
OUT_OF_SCOPE_HOST = "etestavimas.lt"