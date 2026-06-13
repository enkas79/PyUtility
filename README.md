🛠️ Python Utility Suite

Una collezione completa di strumenti di utilità sviluppati in Python con interfaccia grafica PyQt6, progettata per semplificare la gestione quotidiana di immagini e documenti PDF.

👤 **Autore e Versione**
- **Autore:** Enrico Martini
- **Versione Corrente:** 1.2.0

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
   - **Ricerca Mirata:** Filtra per estensione (PDF, DOCX, XLSX, ecc.) e parole chiave.
   - **Azioni Rapide:** Permette di copiare o spostare i file trovati verso una cartella di destinazione specifica direttamente dall'interfaccia.
   - **Multithreading:** La ricerca avviene in background per non bloccare l'interfaccia.

5. 📄 **PDF Plus (Unione PDF)**
   - **Merge Intelligente:** Unisce più PDF in un unico file.
   - **Limite Dimensioni:** Include una logica di split automatico se il file risultante supera i 99MB.
   - **Importazione Facile:** Supporta l'aggiunta di singoli file o di intere cartelle.

6. ✂️ **PDF Splitter** *(Nuovo in v1.2.0)*
   - **Pagine Singole:** Divide ogni pagina del PDF in un file separato.
   - **Intervallo di Pagine:** Estrae un intervallo specifico di pagine.
   - **N Pagine per File:** Divide il PDF in file con un numero personalizzabile di pagine.

7. 📝 **PDF to Word Converter**
   - **Conversione Fedele:** Trasforma i documenti .pdf in file .docx editabili.
   - **Interfaccia Semplificata:** Processo guidato "seleziona e converti" con feedback visivo immediato.

---

🛠️ **Requisiti Tecnici**
Per eseguire la suite, è necessario installare le seguenti librerie Python:

```bash
pip install -r requirements.txt
```

Oppure manualmente:
```bash
pip install PyQt6==6.6.1 Pillow==10.2.0 PyPDF2==3.0.1 pdf2docx==0.8.5 pyinstaller==6.0.0
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
   python MainSuite.py
   ```

---

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
