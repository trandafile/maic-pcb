# Project Specifications: PCB Stack-up & Via Visualizer

## 1. Descrizione del Progetto
Sviluppo di un'applicazione web interattiva basata su Python e Streamlit per la definizione, documentazione e visualizzazione avanzata (2D e 3D) di stack-up di circuiti stampati (PCB). Il tool permette la gestione fluida di strati metallici, dielettrici e diverse tipologie di via (Through-hole, Blind, Buried, Laser Microvia), garantendo un output visivo rigoroso per la documentazione tecnica.

## 2. Architettura del Software
* **Frontend e Framework:** Streamlit (Python).
* **Motore Grafico:** Plotly (per rendering interattivo 2D, 3D ed esportazione vettoriale).
* **Manipolazione Dati:** Pandas (per gestione DataFrame, import/export e logiche di posizionamento).
* **Storage e I/O Dati:** Memoria di stato di Streamlit (`st.session_state`) per l'esecuzione; file JSON e `.xlsx` per il salvataggio/caricamento dei progetti; Google Sheets (tramite API/st.connection) o Excel locale per la libreria centralizzata dei materiali.

## 3. Gestione della Libreria Materiali (Database Esterno)
La libreria dei materiali (ospitata su Google Sheets o Excel condiviso) deve avere una struttura gerarchica per prevenire errori di inserimento utente.
* **Campi richiesti:**
    * `Brand` (Marca): es. Isola, Rogers, Panasonic.
    * `Type/Code` (Modello): es. 370HR, 4350B, Megtron 6.
    * `Category` (Categoria): Core, Prepreg, Copper Foil, Solder Mask.
    * `Er` (Costante Dielettrica): Valore numerico.
    * `Df` (Tangente di perdita): Valore numerico (opzionale ma raccomandato).
    * `Available_Thicknesses` (Spessori Disponibili): Array o stringa parsabile di valori reali (es. `[0.05, 0.1, 0.12, 0.2]`) in mm o mils.
* **Logica UI:** L'interfaccia dell'app filtrerà dinamicamente le dropdown: la selezione di un materiale popolerà una seconda dropdown limitata ai soli spessori validi per quel codice specifico.

## 4. Struttura dei Dati del Progetto (JSON / State Dictionary)
Il singolo progetto di stack-up è descritto da due entità principali.

### 4.1. Layers (Ordinati per Z-index dall'alto al basso)
* `id`: Identificativo univoco (es. "L1", "D1").
* `name`: Etichetta editabile dall'utente (es. "Top Copper", "GND").
* `type`: "metal" o "dielectric".
* `material_ref`: Riferimento alla libreria materiali (Brand + Code).
* `thickness`: Spessore selezionato.
* `color_hex`: Codice colore esadecimale (se nullo, si applica la palette di default).

### 4.2. Vias
* `id`: Nome univoco (es. "VIA_L1_L2").
* `type`: "mechanical" (cilindrico) o "laser" (conico/a V).
* `start_layer`: ID del layer superiore di partenza.
* `end_layer`: ID del layer inferiore di arrivo.
* `drill_diameter`: Diametro del foro.
* `pad_diameter`: Diametro della piazzola sui layer di connessione.
* `antipad_diameter`: Diametro del foro di isolamento sui layer attraversati ma non connessi.
* `plating_thickness`: Spessore del rame sulle pareti del foro.
* `fill_type`: "empty" (vuoto), "epoxy" (resina), "copper_plated" (pieno di rame).

## 5. Logiche di Manipolazione dello Stack-up
L'interfaccia deve consentire modifiche dinamiche all'ordine dei layer, preservando l'integrità del progetto:
* **Aggiunta Layer:** Possibilità di inserire un nuovo strato in posizioni intermedie (non solo alla fine).
* **Spostamento Layer:** Comandi per traslare un layer sull'asse Z (es. "Sposta Su", "Sposta Giù" o modifica diretta dell'indice). Il sistema deve ricalcolare in background gli Z-index assoluti.
* **Rimozione Layer:** Eliminazione controllata. Se l'utente tenta di eliminare un layer che funge da `start_layer` o `end_layer` per un Via esistente, il sistema deve bloccare l'azione mostrando un alert, oppure chiedere di eliminare a cascata i Via collegati.

## 6. Gestione Colori e Palette Visiva
L'applicazione include un gestore di colori con palette predefinite studiate per garantire il massimo contrasto tecnico. L'utente può sovrascriverle, ma i default sono ferrei:
* **Metalli (Copper, Copper Foil, Via Plating):**
    * Palette: *Orange Shades* (Sfumature di Arancione).
    * Restrizione: Colori solidi, caldi e ben visibili (es. `#CC5500`, `#FF7F50`).
* **Dielettrici (Core, Prepreg, Solder Mask):**
    * Palette: *Matte Earth Tones* (Toni della terra opachi/freddi).
    * Restrizione: Esclusione categorica di arancioni, rossastri, marroni caldi o senape per evitare confusione con i metalli.
    * Esempi ammessi: Grigio ardesia (`#708090`), Verde oliva smorzato (`#556B2F`), Blu polvere (`#5F7180`).

## 7. Requisiti dell'Interfaccia Utente (UI) e I/O

### 7.1. Controlli Visivi e Viste
* **Sidebar/Top Bar:** Toggles per mostrare/nascondere etichette quote (spessori dielettrici a destra, spessori metalli a sinistra), nomi dei layer editabili e quote dei via.
* **Vista 2D (Cross-Section):** Layout planare tramite Plotly. Asse Y per lo spessore, Asse X discreto per distanziare i via. I metalli sono continui ma interrotti dagli `antipad_diameter` se attraversati da via non connessi.
* **Vista 3D (Esplosa):** Layout spaziale tramite Plotly Graph Objects. Layer renderizzati come `Mesh3d` (dielettrici semi-trasparenti, metalli opachi). Via renderizzati come cilindri/coni.
* **Slider Esplosione 3D:** Controllo che regola parametricamente la distanza (offset Z) tra i layer. A `0` lo stack-up è compatto; aumentando il valore, i layer si separano rivelando la struttura dei via.

### 7.2. Importazione ed Esportazione
* **Gestione Progetti:** Pulsanti per salvare l'intero stato (Layers, Vias, Colori) in un file di configurazione (`.json`) e ricaricarlo.
* **Import/Export Excel:** Esportazione tabellare dei dati dello stack-up in file `.xlsx` formattato, e capacità di importare uno stack-up leggendo i fogli "Layers" e "Vias" da un template `.xlsx`.
* **Export Grafico:** Pulsante per il download vettoriale (`.svg`) della vista attualmente attiva (2D o 3D) per l'inclusione in datasheet e documentazione.

## 8. Fasi di Sviluppo (Roadmap)
1. Inizializzazione app Streamlit, configurazione `st.session_state` e lettura della libreria materiali da Google Sheets / Excel locale.
2. Sviluppo dell'interfaccia CRUD per la manipolazione logica dello stack-up (Aggiungi, Rimuovi, Sposta, con validazione Via).
3. Implementazione del motore di rendering Plotly 2D (prima layer, poi sovrapposizione via con logiche pad/antipad).
4. Implementazione del motore Plotly 3D con calcolo dinamico delle coordinate Z guidato dallo slider di esplosione.
5. Sviluppo del modulo I/O per l'esportazione/importazione massiva in Excel e il salvataggio progetto in JSON.
6. Aggiunta dei pulsanti di esportazione nativa in SVG e rifinitura della palette colori.