# Menù Beauty Garden Banqueting — preventivi

Menù per i preventivi, rifatti da capo in stile minimal secondo il Manuale del marchio,
con gli stessi font dei menù da tavola (Velista e Fraunces).
Sono pensati per essere **stampati e compilati a penna durante il preventivo**.

Il contenuto (piatti, prezzi, condizioni) è separato dalla grafica: si modifica il testo
e i PDF si rigenerano tutti con la stessa impaginazione.

> **Stato: pilota.** Per ora sono stati rifatti 2 menù per validare grafica e tono:
> `Matrimonio - Carne Special` e `Banchetti - Buffet Carne Executive`.
> Gli altri si aggiungono allo stesso modo dopo l'approvazione.

## Come è fatto un menù

- **Pagine del menù**: a sinistra le portate, a destra una **colonna di righe per le modifiche
  a penna**, allineata a ogni portata. Le portate che si cambiano più spesso (primi e
  secondi) hanno più righe.
- **Ultima pagina, riepilogo del preventivo**: cosa è incluso, condizioni, supplementi con
  casella da spuntare, e i campi da compilare: sposi o intestatario, data dell'evento,
  adulti, bambini, sala, prezzo del menù (già stampato), supplementi a persona, prezzo
  concordato a persona, totale, data e scadenza del preventivo, altre modifiche, firma.
- Matrimonio: 3 pagine. Banchetti: 2 pagine.

## Cosa c'è

| Cartella / file | Contenuto |
|---|---|
| `pdf/` | **I menù pronti da stampare** (generati, non modificarli a mano) |
| `listino/comune.yaml` | Testi comuni: contatti, intro, incluso, condizioni, supplementi, validità |
| `listino/menu/*.yaml` | Un file per menù: nome, prezzo, portate |
| `modello/` | Grafica: stile, logo vettoriale, font |
| `genera.py` | Script che crea i PDF |
| `*.pdf` nella cartella principale | Menù originali 2026 (CorelDRAW), lasciati come riferimento |

## Come modificare un menù

1. Apri il file in `listino/menu/` (anche da GitHub: icona della matita).
2. Cambia il testo. Il prezzo va scritto come numero, senza €: `prezzo: 115`.
3. Rigenera i PDF (vedi sotto).

Per una condizione valida per tutti i menù (es. un supplemento sala), modifica solo `listino/comune.yaml`.

### Struttura di un menù

```yaml
linea: matrimonio          # matrimonio | banchetti
nome: "Carne Special"
prezzo: 110
sezioni:
  - titolo: "Benvenuto"
    layout: semplice       # voci brevi, una per riga
    voci: ["Cocktail alcolico e analcolico", "Rustici vari"]
  - titolo: "Antipasti"
    layout: isole          # nome + descrizione, su 2 colonne
    voci:
      - nome: "Isola della Brace"
        desc: "Carni pregiate cotte al momento"
  - titolo: "Primi piatti"
    pagina_nuova: true     # inizia una nuova pagina
    layout: piatti         # piatti serviti
    righe_note: 5          # righe per le modifiche a penna (minimo 3 se non indicato)
    voci: ["Risotto ..."]
    contorno: "..."        # facoltativo
    nota_sostituzioni: true
  - titolo: "Dolci"
    layout: elenco         # elenco su 2 colonne
    evidenza: "Torta nuziale ..."
    voci: ["Cannoli assortiti", "..."]
```

Voci aggiuntive solo per un menù: `incluso_extra:` e `condizioni_extra:`.

## Come generare i PDF

Serve Python 3 con `pip install pyyaml jinja2` e Google Chrome (o Chromium/Edge) installato.

```bash
python genera.py
```

Lo script controlla gli errori più comuni (prezzo non numerico, sezioni vuote, nomi
duplicati) e avvisa se un menù supera le pagine previste.

### Preventivo precompilato

```bash
python genera.py matrimonio-carne-special --cliente "Nome e Cognome" --data-evento 12/06/2027 --adulti 120 --bambini 8 --sala "Sala Luxury" --note "..."
```

Il PDF finisce in `preventivi/`, con data del preventivo e scadenza calcolate in automatico.
Prezzo concordato, supplementi e totale restano da scrivere a penna.
La cartella `preventivi/` **non viene pubblicata su GitHub** perché contiene dati dei clienti.

## Font

- **Velista** (Toni Studio, licenza commerciale): titoli, nomi delle portate e prezzo.
  È solo maiuscolo e non ha il simbolo €, per questo i prezzi sono scritti "110 euro a persona".
  **Non va pubblicato su GitHub**: lo script lo cerca in `modello/font/privati/VELISTA.ttf`
  (cartella esclusa da git) oppure lo estrae da `velista.zip`.
- **Fraunces** (licenza libera OFL): tutto il resto. In `modello/font/` ci sono versioni
  statiche ricavate dal file variabile alla misura ottica per il testo (10pt).

## Colori e logo

- Colori presi dai campioni del manuale: verde `#2B392A`, oro `#C79A4E`, crema `#EDE5D4`,
  nero `#201F1B`. I codici scritti nel manuale non corrispondono ai campioni
  (es. "#3d2a65e" non è un colore valido; crema e nero sono etichettati entrambi "#292820").
- Logo estratto in vettoriale dal manuale (`modello/logo/`), in oro, verde, nero e bianco.

## Da decidere prima di estendere a tutti i menù

Le condizioni nei PDF originali non erano uguali tra un menù e l'altro. In `comune.yaml`
è stata usata la versione del Carne Special (coincide con la maggioranza), ma va confermata:

- Pesce Superior: vale € 135 (`158 PESCE SUPERIOR 2026.pdf`) o € 128 (`Backup_di_128 …`)?
- Supplemento € 5: Sala Ducale, Sala Regina o entrambe? Sala riservata: minimo 80 o 60 persone?
- I prezzi sono IVA inclusa?
- "Esclusiva a pranzo" e "Sabato no sconti": solo menù top o tutti?
- Pesce Gold: parcheggio custodito o non custodito?
- Nomi duplicati nei banchetti: "Buffet Carne Classic" (€ 70 e € 78), "Buffet Pesce Banchetto" (€ 88 e € 98).
