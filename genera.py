#!/usr/bin/env python3
"""
Genera i PDF dei menù a partire dai file in listino/.

Uso:
  python genera.py                          -> tutti i menù in pdf/
  python genera.py matrimonio-carne-special -> solo quel menù

Preventivo precompilato (finisce in preventivi/):
  python genera.py matrimonio-carne-special --cliente "Anna e Marco" \
      --data-evento 12/06/2027 --adulti 120 --bambini 8 --sala "Sala Luxury" --note "..."

Requisiti: Python 3 con i pacchetti pyyaml e jinja2 (pip install pyyaml jinja2)
e Google Chrome o Chromium installato.
"""
import argparse
import calendar
import datetime as dt
import os
import platform
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
USCITA_PREVENTIVI = RADICE / "preventivi"

ETICHETTE_LINEA = {"matrimonio": "Matrimonio", "banchetti": "Banchetti"}
PAGINE_MASSIME = {"matrimonio": 2, "banchetti": 1}
LAYOUT_VALIDI = {"linea", "isole", "piatti", "elenco"}


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
        if not s.get("voci") and not s.get("evidenza"):
            errori.append(f"sezione {i} ('{s.get('titolo')}'): nessuna voce")
    return [f"{slug}: {e}" for e in errori]


def aggiungi_mesi(data: dt.date, mesi: int) -> dt.date:
    m = data.month - 1 + mesi
    anno, mese = data.year + m // 12, m % 12 + 1
    giorno = min(data.day, calendar.monthrange(anno, mese)[1])
    return dt.date(anno, mese, giorno)


def dati_preventivo(args, comune: dict) -> dict:
    vuoto = {k: "" for k in ("cliente", "data_evento", "ospiti", "sala", "data_preventivo", "scadenza", "note")}
    if not args.cliente:
        return vuoto
    oggi = dt.date.today()
    mesi = int(re.match(r"\d+", comune["validita_preventivo"]).group())
    ospiti = ""
    if args.adulti is not None:
        ospiti = f"{args.adulti} · {args.bambini if args.bambini is not None else 0}"
    return {
        "cliente": args.cliente,
        "data_evento": args.data_evento or "",
        "ospiti": ospiti,
        "sala": args.sala or "",
        "data_preventivo": oggi.strftime("%d/%m/%Y"),
        "scadenza": aggiungi_mesi(oggi, mesi).strftime("%d/%m/%Y"),
        "note": args.note or "",
    }


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
    parser.add_argument("--cliente", help="nome degli sposi o dell'intestatario")
    parser.add_argument("--data-evento")
    parser.add_argument("--adulti", type=int)
    parser.add_argument("--bambini", type=int)
    parser.add_argument("--sala")
    parser.add_argument("--note")
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
    if args.cliente and len(file_menu) != 1:
        sys.exit("Per un preventivo precompilato indica un solo menù.")

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
    chrome = trova_chrome()
    preventivo = dati_preventivo(args, comune)

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
            email_piede=c["email"] if linea == "matrimonio" else f"{c['email_info']}  ·  {c['email']}",
            p=preventivo,
        )
        nome_file = f"{ETICHETTE_LINEA[linea]} - {menu['nome']}.pdf"
        if args.cliente:
            data = dt.date.today().strftime("%Y-%m-%d")
            nome_file = f"Preventivo {data} - {args.cliente} - {menu['nome']}.pdf"
            destinazione = USCITA_PREVENTIVI / nome_file
        else:
            destinazione = USCITA_MENU / nome_file
        stampa_pdf(chrome, html, destinazione)
        if args.html:
            destinazione.with_suffix(".html").write_text(html, encoding="utf-8")
        pagine = conta_pagine(destinazione)
        avviso = ""
        if pagine > PAGINE_MASSIME[linea]:
            avviso = f"  ⚠ {pagine} pagine (previste {PAGINE_MASSIME[linea]}): accorcia i testi"
        print(f"✓ {destinazione.relative_to(RADICE)}  ({pagine} pag.){avviso}")


if __name__ == "__main__":
    main()
