🛠️ Python Utility Suite

Una collezione completa di strumenti di utilità sviluppati in Python con interfaccia grafica PyQt6, progettata per semplificare la gestione quotidiana di immagini e documenti PDF.

👤 **Autore e Versione**
- **Autore:** Enrico Martini
- **Versione Corrente:** 1.6.0

🚀 **Funzionalità Incluse**
La suite integra **otto** strumenti principali, accessibili da un unico hub centrale:

1. 🖼️ **Image Converter & Resizer**
   - **Conversione Formati:** Supporta JPG, PNG, WEBP, BMP, ICO e TIFF.
   - **Ridimensionamento Intelligente:** Ridimensiona per percentuale, larghezza fissa o altezza fissa mantenendo le proporzioni.
   - **Elaborazione Batch:** Gestisce più file simultaneamente con barra di progressione e report finale.

2. 🧩 **Image Merger (Unisci Immagini)**
   - **Unione Immagini:** Unisce più immagini in un'unica immagine.
   - **Direzione Personalizzabile:** Verticale (dall'alto al basso) o orizzontale (da sinistra a destra).
   - **Drag-and-Drop:** Riordina le immagini trascinandole nella lista.

3. 🎨 **Image Watermark** *(Nuovo in v1.2.0)*
   - **Watermark di Testo:** Aggiungi testo personalizzato con font, colore e dimensione regolabili.
   - **Watermark Immagine:** Usa un'immagine come watermark (es. logo).
   - **Posizione Flessibile:** 9 posizioni predefinite (centro, angoli, bordi).
   - **Opacità Regolabile:** Controlla la trasparenza del watermark (1%-100%).

4. 🔍 **Ricerca & Gestione Documenti**
   - **Ricerca Mirata:** Filtra per una o più estensioni (PDF, DOCX, XLSX, ecc.) e parole chiave, con o senza sottocartelle.
   - **Azioni Rapide:** Copia o sposta i file trovati verso una cartella di destinazione, con barra di avanzamento; i file omonimi non vengono mai sovrascritti.
   - **Multithreading:** Ricerca e copia/spostamento avvengono in background e possono essere interrotte.

5. 📋 **Lista File Cartella** *(Nuovo in v1.3.0)*
   - **Elenco File:** Genera la lista dei file di una cartella (con o senza sottocartelle).
   - **Filtro Estensione:** Una o più estensioni libere (es. `pdf, docx`) o preset (Documenti, Immagini, Audio/Video, Archivi).
   - **Filtro Dimensione:** Dimensione minima e/o massima in B, KB, MB, GB.
   - **Esportazione:** CSV (compatibile Excel), TXT o copia dei percorsi negli appunti; tabella ordinabile per nome, dimensione e data.

6. 📄 **PDF Plus (Unione PDF)**
   - **Merge Intelligente:** Unisce più PDF in un unico file.
   - **Limite Dimensioni:** Include una logica di split automatico se il file risultante supera i 99MB.
   - **Importazione Facile:** Supporta l'aggiunta di singoli file o di intere cartelle.

7. ✂️ **PDF Splitter** *(Nuovo in v1.2.0)*
   - **Pagine Singole:** Divide ogni pagina del PDF in un file separato.
   - **Intervallo di Pagine:** Estrae un intervallo specifico di pagine.
   - **N Pagine per File:** Divide il PDF in file con un numero personalizzabile di pagine.

8. 📝 **PDF to Word Converter**
   - **Conversione Fedele:** Trasforma i documenti .pdf in file .docx editabili.
   - **Interfaccia Semplificata:** Processo guidato "seleziona e converti" con feedback visivo immediato.

---

🛠️ **Requisiti Tecnici**
Serve **Python 3.10 o superiore**. Le versioni delle librerie (PyQt6, Pillow, PyPDF2, pdf2docx, PyMuPDF, PyInstaller) sono fissate in `requirements.txt`, usato anche dalla build CI:

```bash
pip install -r requirements.txt        # esecuzione
pip install -r requirements-dev.txt    # sviluppo: aggiunge pytest e ruff
```

📦 **Installazione e Utilizzo**
1. Clona la repository:
   ```bash
   git clone https://github.com/enkas79/PyUtility.git
   cd PyUtility
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Avvia l'applicazione principale:
   ```bash
   python src/main.py
   ```

4. Test e lint (eseguiti anche da GitHub Actions a ogni push, e prima di ogni build):
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ruff check . --fix
   ```

🗂️ **Struttura del Progetto**
- `src/main.py` – hub principale (entry point) e registro dei tool.
- `src/<Tool>.py` – finestre dei singoli strumenti (ereditano da `BaseWindow`).
- `src/base_window.py` – classe base: stile, menu **Aiuto** standard, logging.
- `src/styles.py` – foglio di stile QSS centralizzato (palette WCAG AA).
- `src/updater.py` / `src/update_manager.py` – autoupdate (logica / thread e dialoghi Qt).
- `src/image_core.py`, `src/pdf_core.py` – logica di immagini e PDF senza Qt (testata).
- `src/file_lister_core.py`, `src/file_workers.py` – logica e worker condivisi.
- `tests/` – suite `pytest`; `version.txt` – versione corrente (trigger della build).

---

📝 **Novità nella Versione 1.6.0**
- **Nessuna sovrascrittura**: Image Converter non sostituisce più l'originale (es. PNG → PNG nella stessa cartella) né i file omonimi; PDF Splitter, PDF Plus e PDF to Word aggiungono un suffisso ' (1)' invece di sovrascrivere.
- **PDF Plus**: il riepilogo elenca i file creati; corretto un caso in cui un file 'NN - Main.pdf' già esistente veniva sovrascritto; messaggio chiaro per i PDF protetti da password.
- **PDF to Word**: il convertitore viene chiuso anche in caso di errore.
- **Aggiornamenti verificati**: l'installer scaricato viene controllato con il checksum SHA-256 pubblicato nella release; se non corrisponde viene eliminato e non eseguito.
- **CI**: lint e test a ogni push; la build degli installer parte solo se passano e usa le versioni fissate in `requirements.txt` (che prima indicava una versione inesistente di pdf2docx).
- Logica di immagini e PDF separata dall'interfaccia (`image_core.py`, `pdf_core.py`) e coperta da test.

📝 **Novità nella Versione 1.5.0**
- **Aggiornamento automatico**: all'avvio (e da *Aiuto > Controlla Aggiornamenti*) la suite verifica le GitHub Releases, mostra il changelog, scarica l'installer in background e avvia l'installazione.
- **Menu Aiuto uniforme** in tutte le finestre: Guida (F1), Controlla Aggiornamenti, Informazioni (autore e versione).
- **Stile unificato**: tutti i tool usano il foglio di stile centralizzato; palette con contrasto WCAG AA e spaziature su griglia 4/8 px.
- Codice spostato in `src/` (avvio: `python src/main.py`); workflow rinominato in `build-installers.yml`.
- Log salvato nella cartella dati dell'utente (prima: crash se la cartella corrente non era scrivibile).
- **PDF to Word**: un file `.PDF` (maiuscolo) non viene più sovrascritto dal `.docx`.
- **Image Merger**: ordine corretto anche con file omonimi in cartelle diverse.

📝 **Novità nella Versione 1.4.0**
- Nuova **icona** dell'applicazione (finestre, eseguibile Windows, installer e pacchetto Linux). Sorgente vettoriale in `assets/icon.svg`, rigenerabile con `python tools/build_icons.py`.
- **Ricerca Documenti** riscritta sul motore condiviso di Lista File: copia/sposta in background, nessuna sovrascrittura, ricerca interrompibile, tabella ordinabile per dimensione.
- **Image Watermark**: corretto il watermark di testo (incompatibile con Pillow 10) e l'opacità; output salvato con estensione `.png` coerente.
- Corretto l'avvio stand-alone di Image Watermark e PDF Splitter.

📝 **Novità nella Versione 1.3.0**
- Nuovo tool **Lista File Cartella** con filtri per estensione e dimensione ed export CSV/TXT.
- **Caricamento modulare dei tool**: un modulo con dipendenze mancanti non blocca più gli altri.
- **Build CI**: aggiunte le dipendenze Pillow e PyPDF2 mancanti nel workflow.
- **Test**: suite `pytest` in `tests/`.

📝 **Novità nella Versione 1.2.0**
- Aggiunti **2 nuovi tool**: PDF Splitter e Image Watermark.
- **Refactoring del codice**: Introduzione di una classe base (`BaseWindow`) per ridurre la ridondanza.
- **Stili centralizzati**: Tutti gli stili CSS sono ora gestiti in un file dedicato (`styles.py`).
- **Logging**: Aggiunto supporto per il logging delle operazioni e degli errori.
- **Type Hints**: Migliorata la tipizzazione del codice per una maggiore manutenibilità.

---

🐛 **Segnalazione Bug e Contributi**
- **Segnala un bug:** Apri una [issue](https://github.com/enkas79/PyUtility/issues) su GitHub.
- **Contribuisci:** Le pull request sono benvenute! Assicurati di seguire le linee guida del progetto.

---

📜 **Licenza**
Questo progetto è distribuito sotto **Licenza MIT**. Vedi il file [LICENSE](LICENSE) per i dettagli.
