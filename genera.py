#!/usr/bin/env python3
"""
Genera i PDF dei menù a partire dai file in listino/.

Uso:
  python genera.py                          -> tutti i menù in pdf/
  python genera.py matrimonio-carne-special -> solo quel menù

I PDF si stampano in serie (A4, fronte-retro) e il preventivo si compila a penna.

Requisiti: Python 3 con i pacchetti pyyaml e jinja2 (pip install pyyaml jinja2)
e Google Chrome o Chromium installato.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

RADICE = Path(__file__).resolve().parent
LISTINO = RADICE / "listino"
MODELLO = RADICE / "modello"
USCITA_MENU = RADICE / "pdf"

ETICHETTE_LINEA = {"matrimonio": "Matrimonio", "banchetti": "Banchetti"}
# Facciate previste: sempre pari, perché si stampa fronte-retro.
PAGINE_PREVISTE = {"matrimonio": 4, "banchetti": 2}
# Pagine di riepilogo: il matrimonio ha condizioni/extra e preventivo su due
# facciate separate, i banchetti tutto su una.
RIEPILOGO = {
    "matrimonio": {"pagina_separata": True, "righe_extra": 12, "righe_note": 9},
    "banchetti": {"pagina_separata": False, "righe_extra": 4, "righe_note": 3},
}
LAYOUT_VALIDI = {"semplice", "isole", "piatti", "elenco"}
VELISTA = MODELLO / "font" / "privati" / "VELISTA.ttf"


def prepara_velista() -> None:
    """Velista è un font commerciale: non va pubblicato su GitHub.
    Lo script lo cerca in modello/font/privati/ oppure lo estrae da velista.zip."""
    if VELISTA.exists():
        return
    archivio = RADICE / "velista.zip"
    if archivio.exists():
        import zipfile
        with zipfile.ZipFile(archivio) as z:
            nome = next((n for n in z.namelist() if n.lower().endswith("velista.ttf")), None)
            if nome:
                VELISTA.parent.mkdir(parents=True, exist_ok=True)
                VELISTA.write_bytes(z.read(nome))
                return
    sys.exit("Manca il font Velista: copia VELISTA.ttf in modello/font/privati/ (cartella esclusa da git).")


def trova_chrome() -> str:
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for nome in ("chrome-headless-shell", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        percorso = shutil.which(nome)
        if percorso:
            return percorso
    candidati = [
        "/opt/pw-browsers/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidati:
        if Path(c).exists():
            return c
    sys.exit("Chrome/Chromium non trovato. Installalo oppure indica il percorso con la variabile CHROME_PATH.")


def leggi_yaml(percorso: Path) -> dict:
    with open(percorso, encoding="utf-8") as f:
        return yaml.safe_load(f)


def controlla_menu(slug: str, menu: dict) -> list[str]:
    errori = []
    for campo in ("linea", "nome", "prezzo", "sezioni"):
        if campo not in menu:
            errori.append(f"manca il campo '{campo}'")
    if menu.get("linea") not in ETICHETTE_LINEA:
        errori.append(f"linea '{menu.get('linea')}' non valida (usa: {', '.join(ETICHETTE_LINEA)})")
    if not isinstance(menu.get("prezzo"), (int, float)):
        errori.append("il prezzo deve essere un numero, senza simbolo €")
    for i, s in enumerate(menu.get("sezioni") or [], 1):
        if s.get("layout") not in LAYOUT_VALIDI:
            errori.append(f"sezione {i} ('{s.get('titolo')}'): layout '{s.get('layout')}' non valido")
        if "righe_note" in s and not isinstance(s["righe_note"], int):
            errori.append(f"sezione {i} ('{s.get('titolo')}'): righe_note deve essere un numero intero")
        if not s.get("voci") and not s.get("evidenza"):
            errori.append(f"sezione {i} ('{s.get('titolo')}'): nessuna voce")
    return [f"{slug}: {e}" for e in errori]


def conta_pagine(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def stampa_pdf(chrome: str, html: str, destinazione: Path) -> None:
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        sorgente = Path(tmp) / "menu.html"
        sorgente.write_text(html, encoding="utf-8")
        comando = [
            chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
            "--disable-background-networking", "--disable-sync", "--disable-extensions",
            "--no-pdf-header-footer", "--print-to-pdf-no-header",
            f"--user-data-dir={Path(tmp) / 'profilo'}",
            f"--print-to-pdf={destinazione}", sorgente.as_uri(),
        ]
        esito = subprocess.run(comando, capture_output=True, text=True, timeout=120)
        if esito.returncode != 0 or not destinazione.exists():
            sys.exit(f"Errore di Chrome durante la stampa di {destinazione.name}:\n{esito.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera i PDF dei menù Beauty Garden.")
    parser.add_argument("menu", nargs="*", help="nome del file in listino/menu senza .yaml (vuoto = tutti)")
    parser.add_argument("--html", action="store_true", help="salva anche l'HTML accanto al PDF (per controlli)")
    args = parser.parse_args()

    comune = leggi_yaml(LISTINO / "comune.yaml")
    file_menu = sorted((LISTINO / "menu").glob("*.yaml"))
    if args.menu:
        richiesti = set(args.menu)
        file_menu = [f for f in file_menu if f.stem in richiesti]
        mancanti = richiesti - {f.stem for f in file_menu}
        if mancanti:
            sys.exit(f"Menù non trovati: {', '.join(sorted(mancanti))}")

    menus = {f.stem: leggi_yaml(f) for f in file_menu}
    errori = [e for slug, m in menus.items() for e in controlla_menu(slug, m)]
    nomi = {}
    for slug, m in menus.items():
        chiave = (m.get("linea"), str(m.get("nome")).lower())
        if chiave in nomi:
            errori.append(f"{slug}: stesso nome di {nomi[chiave]} ('{m.get('nome')}') nella stessa linea")
        nomi[chiave] = slug
    if errori:
        sys.exit("Correggi prima questi errori:\n  - " + "\n  - ".join(errori))

    env = Environment(loader=FileSystemLoader(MODELLO), autoescape=True)
    modello = env.get_template("menu.html.j2")
    prepara_velista()
    chrome = trova_chrome()

    for slug, menu in menus.items():
        linea = menu["linea"]
        c = comune["contatti"]
        html = modello.render(
            base=MODELLO.as_uri() + "/",
            menu=menu,
            comune=comune,
            c=c,
            etichetta_linea=ETICHETTE_LINEA[linea],
            intro=comune["intro"].get(linea, ""),
            incluso=(comune.get(f"incluso_{linea}") or []) + (menu.get("incluso_extra") or []),
            condizioni=(comune.get(f"condizioni_{linea}") or []) + (menu.get("condizioni_extra") or []),
            supplementi=comune.get(f"supplementi_{linea}") or [],
            email_piede=c["email"] if linea == "matrimonio" else f"{c['email_info']}\\2003 {c['email']}",
            r=RIEPILOGO[linea],
        )
        destinazione = USCITA_MENU / f"{ETICHETTE_LINEA[linea]} - {menu['nome']}.pdf"
        stampa_pdf(chrome, html, destinazione)
        if args.html:
            destinazione.with_suffix(".html").write_text(html, encoding="utf-8")
        pagine = conta_pagine(destinazione)
        avviso = ""
        if pagine != PAGINE_PREVISTE[linea]:
            avviso = (f"  ⚠ {pagine} facciate invece di {PAGINE_PREVISTE[linea]}: "
                      "in fronte-retro resterebbero facciate vuote o fogli in più; accorcia o allunga i testi")
        print(f"✓ {destinazione.relative_to(RADICE)}  ({pagine} facciate){avviso}")


if __name__ == "__main__":
    main()
