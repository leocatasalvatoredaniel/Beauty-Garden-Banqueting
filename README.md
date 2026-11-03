# Menù Beauty Garden Banqueting — preventivi

Menù per i preventivi, rifatti da capo in stile minimal secondo il Manuale del marchio,
con gli stessi font dei menù da tavola (Velista e Fraunces).
Sono pensati per essere **stampati in serie (A4 fronte-retro, stampante d'ufficio a colori)
e compilati a penna durante il preventivo**.

Il contenuto (piatti, prezzi, condizioni) è separato dalla grafica: si modifica il testo
e i PDF si rigenerano tutti con la stessa impaginazione.

> **Stato: pilota.** Per ora sono stati rifatti 2 menù per validare grafica e tono:
> `Matrimonio - Carne Special` e `Banchetti - Buffet Carne Executive`.
> Gli altri si aggiungono allo stesso modo dopo l'approvazione.

## Come è fatto un menù

| | Matrimonio (2 fogli A4 fronte-retro, pinzati) | Banchetti (1 foglio A4 fronte-retro) |
|---|---|---|
| Facciata 1 | Nome, prezzo, benvenuto, antipasti | Tutto il menù |
| Facciata 2 | Primi, secondi, dolci, bar | Condizioni, extra e preventivo |
| Facciata 3 | Incluso, condizioni e supplementi, extra e aggiunte | |
| Facciata 4 | Preventivo da compilare | |

Spazi per la penna, uno per ogni cosa che si annota durante il preventivo:

- **Cambi di piatti**: colonna di righe "Modifiche" accanto a ogni portata (più righe per primi e secondi).
- **Aggiunte ed extra**: tabella a righe con colonna del prezzo.
- **Prezzi e sconti**: prezzo del menù (stampato), supplementi, extra, sconto, prezzo concordato a persona, totale. I supplementi sala si spuntano.
- **Dati e logistica**: sposi o intestatario, telefono, email, data, pranzo o cena, adulti, bambini, sala, intolleranze e allergie, note.

Lo script avvisa se un menù non ha il numero esatto di facciate (4 o 2): in fronte-retro
una facciata in più o in meno significa un foglio sprecato o una pagina bianca.

### Stampa

- Formato A4, **scala 100% / dimensioni effettive** (non "adatta alla pagina"), fronte-retro sul lato lungo.
- Carta non patinata (usomano) da almeno 90–100 g: la penna scrive meglio e non trapassa.
- Le righe per scrivere sono grigie piene, non trasparenti, così escono nitide anche dalle stampanti d'ufficio.

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
duplicati) e il numero di facciate. Il numero di righe di extra e note nelle pagine di
riepilogo si regola in `genera.py` (`RIEPILOGO`).

## Scelte grafiche

Riviste con le skill `impeccable` (critica, tipografia, impaginazione, rifinitura) e
`minimalist-ui`:

- sei ruoli tipografici fissi (36 / 14 / 11 / 9,5 / 8 / 7 pt) invece di dimensioni sparse;
- testo allineato a sinistra, niente etichette maiuscole spaziate, niente separatori decorativi;
- colore usato con parsimonia: verde per titoli e piatti, oro solo per logo e caselle.

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
