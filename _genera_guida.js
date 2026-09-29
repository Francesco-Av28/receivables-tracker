// Genera GUIDA SCADENZIARIO.docx (versione bianca, senza dati dello studio)
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, LevelFormat, AlignmentType, BorderStyle, WidthType,
        ShadingType, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const margini = { top: 80, bottom: 80, left: 120, right: 120 };

const t = (testo, opz = {}) => new Paragraph({ children: [new TextRun({ text: testo, ...opz })], spacing: { after: 120 } });
const h1 = (testo) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(testo)] });
const h2 = (testo) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(testo)] });
const punto = (testo) => new Paragraph({ numbering: { reference: "bullets", level: 0 },
  children: [new TextRun(testo)], spacing: { after: 80 } });
const passo = (testo) => new Paragraph({ numbering: { reference: "passi", level: 0 },
  children: [new TextRun(testo)], spacing: { after: 80 } });
const passo2 = (testo) => new Paragraph({ numbering: { reference: "passi2", level: 0 },
  children: [new TextRun(testo)], spacing: { after: 80 } });

function rigaTab(cells, intestazione = false) {
  return new TableRow({ children: cells.map((c, i) => new TableCell({
    borders, margins: margini,
    width: { size: i === 0 ? 2800 : 6226, type: WidthType.DXA },
    shading: intestazione ? { fill: "1A3A5C", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ children: [new TextRun({ text: c, bold: intestazione,
      color: intestazione ? "FFFFFF" : "000000" })] })],
  })) });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        run: { size: 32, bold: true, font: "Arial", color: "1A3A5C" },
        paragraph: { spacing: { before: 280, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        run: { size: 26, bold: true, font: "Arial", color: "2D5687" },
        paragraph: { spacing: { before: 220, after: 140 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "passi", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "passi2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2000, after: 200 },
        children: [new TextRun({ text: "SCADENZIARIO", bold: true, size: 56, color: "1A3A5C" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 3000 },
        children: [new TextRun({ text: "Guida all’uso — gestione fatture emesse e incassi dello studio", size: 28, color: "44586C" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Gestione fatture emesse e incassi — Settembre 2026", size: 20, color: "708090" })] }),
      new Paragraph({ children: [new PageBreak()] }),

      h1("1. Che cos’è"),
      t("SCADENZIARIO è un programma che tiene la contabilità delle fatture emesse ai clienti: le smista automaticamente in una cartella per ogni cliente, registra gli incassi, timbra i PDF delle fatture pagate e mostra sempre chi deve ancora pagare e da quanto tempo. Non serve internet e nessun dato esce dallo studio."),
      t("Tutti i dati (Excel, INBOX, cartelle dei clienti, archivio) stanno nella cartella “dati”, che il programma crea da solo, vuota, al primo avvio accanto all’exe. Non c’è password: il programma si apre direttamente. Se più PC devono lavorare sugli stessi dati, la cartella “dati” può stare in una cartella condivisa in rete (capitolo 2, “Dati comuni a più PC”).", { bold: true }),

      h1("2. Installazione su un nuovo PC"),
      passo("Copiare l’intera cartella “SCADENZIARIO” dallo ZIP in una posizione comoda del PC (per esempio il Desktop o C:\\)."),
      passo("Aprire la cartella e fare doppio clic su SCADENZIARIO.exe (dentro la sottocartella con lo stesso nome)."),
      passo("Si apre una finestra nera (va lasciata aperta: è il motore del programma) e dopo qualche secondo si apre il browser direttamente sul Riepilogo (non c’è password)."),
      passo("Solo la prima volta: aprire la pagina “Impostazioni” (menu in alto) e compilare i dati dello studio: nome, P.IVA, codice fiscale, indirizzo, telefono, e-mail. Compaiono nei PDF (report e schede cliente) e servono all’Analisi fatture per distinguere la P.IVA dello studio da quella del cliente."),
      t("Per chiudere il programma: chiudere la finestra nera. I dati restano salvati nella cartella “dati”.", { italics: true }),
      t("Se il programma è già aperto sul PC e si fa di nuovo doppio clic, non succede nulla di male: si riapre solo il browser sulla schermata dell'app.", { italics: true }),

      h2("Dati comuni a più PC (cartella in rete)"),
      t("Di norma ogni installazione ha i suoi dati. Per far lavorare più PC sugli stessi dati:"),
      passo2("Creare in una cartella condivisa di rete (NAS o PC server) una cartella, per esempio \\\\NAS\\Condivisa\\SCADENZIARIO."),
      passo2("Su OGNI PC, accanto a SCADENZIARIO.exe, creare con Blocco note un file chiamato percorso_dati.txt con una sola riga: il percorso della cartella dati in rete, per esempio \\\\NAS\\Condivisa\\SCADENZIARIO\\dati"),
      passo2("Avviare il programma: la prima volta crea da solo la cartella dati vuota in rete; gli altri PC la trovano già pronta. Se un PC aveva già dei dati, copiare prima la sua cartella “dati” in rete."),
      t("Per tornare ai dati locali basta eliminare (o svuotare) percorso_dati.txt. Con i dati in rete: registrazioni UNA postazione alla volta. Attenzione: senza password chiunque usi un PC con il programma vede i dati.", { italics: true }),

      h2("Versione alternativa per tecnici (senza .exe)"),
      t("Nella cartella “versione-python” ci sono gli stessi programmi in formato sorgente. Servono solo se l’exe non funzionasse: installare Python 3.12 o superiore da python.org (spuntando “Add to PATH”), aprire il Prompt dei comandi nella cartella e digitare: pip install -r requisiti.txt — poi: python app.py"),

      h1("3. Analisi fatture: smistare le nuove, togliere quelle rimosse"),
      passo2("Salvare i PDF delle fatture emesse nella cartella dati\\INBOX (la pagina “Impostazioni” mostra dove si trova la cartella dati)."),
      passo2("Nell’app aprire la pagina “Analisi fatture” e premere “Analizza”. L’app legge i PDF nuovi nella INBOX e, nello stesso passaggio, controlla le cartelle dei clienti (dati\\CLIENTI)."),
      passo2("Controllare l’anteprima: per ogni PDF l’app mostra il cliente riconosciuto (dalla Partita IVA), il numero, la data, la scadenza e l’importo."),
      passo2("Se è tutto giusto, premere “Conferma”: il pulsante dice esattamente quante fatture registra e quante elimina."),
      t("Cosa succede alla conferma:"),
      punto("ogni PDF viene spostato nella cartella del suo cliente (dati\\CLIENTI) e rinominato in modo ordinato;"),
      punto("la fattura viene registrata come credito aperto con la sua scadenza;"),
      punto("se il cliente non esiste ancora, viene creato automaticamente in anagrafica (con ragione sociale, P.IVA e codice fiscale letti dalla fattura) insieme alla sua cartella: l’anteprima lo segnala con “NUOVO:”. Funziona anche per le persone fisiche senza P.IVA (basta il codice fiscale). Conviene poi controllare la scheda nella pagina “Clienti” (per le persone fisiche separare cognome e nome)."),
      t("I PDF che l’app non riesce a leggere restano nella INBOX con il motivo dell’errore: si possono registrare a mano (paragrafo qui sotto) o chiedere assistenza.", { italics: true }),
      h2("Togliere una fattura dalle cartelle"),
      t("Per eliminare una fattura registrata basta cancellare (o spostare via) il suo PDF dalla cartella del cliente in dati\\CLIENTI e poi premere “Analizza”: l’app la elenca nel riquadro “Fatture da eliminare — PDF tolto dalla cartella del cliente” e, alla conferma, la cancella dai conti. Se su quella fattura c’erano già pagamenti registrati, vengono annullati insieme (l’anteprima lo dice riga per riga); se un pagamento copriva anche altre fatture, quelle tornano aperte e va registrato di nuovo per la parte giusta."),
      punto("Le fatture saldate (PDF in dati\\SALDATE) non vengono controllate: si eliminano solo da “Tutte le fatture”."),
      punto("Le fatture senza PDF (inserite a mano o storiche) non si possono controllare: l’app dice quante sono."),
      punto("Se il PDF è stato tolto per sbaglio: rimetterlo nella cartella del cliente e ripremere “Analizza”, la fattura non viene eliminata. Una fattura tolta dalla cartella e rimessa nella INBOX viene eliminata e registrata di nuovo pulita nello stesso passaggio."),
      punto("I PDF messi a mano nelle cartelle clienti senza passare dall’app vengono solo segnalati (“PDF non registrati”): per registrarli spostarli nella INBOX o usare “Nuova fattura”."),
      punto("Se manca l’intera cartella di un cliente (rinominata o spostata per sbaglio), l’app NON propone di eliminare le sue fatture: la segnala nel riquadro “Cartelle cliente non trovate”. Basta rimettere la cartella col nome originale e ripremere “Analizza”."),
      h2("Inserire una fattura a mano"),
      t("Per le fatture che non passano dalla INBOX (PDF scansionati, fatture senza PDF) c’è il pulsante “Nuova fattura” nel menu in alto (o in “Tutte le fatture”). Si sceglie il cliente dall’elenco oppure “NUOVO CLIENTE” compilando ragione sociale (o cognome), nome, P.IVA e codice fiscale: l’app crea la scheda e la cartella del cliente. Poi numero, data, scadenza e totale della fattura e, se c’è, il PDF da caricare dal PC: viene copiato nella cartella del cliente col nome standard e timbrato ai pagamenti come tutti gli altri. Senza PDF la fattura esiste solo nei conti. Una fattura già registrata (stesso cliente, numero e data) viene rifiutata."),

      h1("4. Registrare un pagamento"),
      t("Quando un cliente paga, aprire la pagina “Pagamenti”:"),
      punto("scegliere il cliente dall’elenco;"),
      punto("scrivere l’importo (per esempio 1.234,56);"),
      punto("la data si può lasciare vuota (vale oggi); la fattura pure (l’app salda prima la più vecchia);"),
      punto("premere “Registra”."),
      t("L’app scala l’importo dalle fatture aperte del cliente e timbra in rosso il PDF della fattura: “ACCONTO € …” se il pagamento è parziale, “PAGATO il …” quando la fattura è saldata. Un pagamento sbagliato si annulla con il pulsante “Annulla” nella stessa pagina: i conti tornano come prima e il timbro di quel pagamento viene tolto dal PDF (l’app conserva una copia pulita di ogni fattura in dati\\ORIGINALI)."),
      t("Si possono registrare solo pagamenti di fatture aperte: se il cliente non ha fatture aperte, o l’importo supera quanto ancora dovuto, l’app rifiuta il pagamento e lo dice. In quel caso manca quasi sempre una fattura da smistare: metterla nella INBOX, registrarla e poi rifare il pagamento. Nell’elenco dei clienti della pagina Pagamenti, accanto al nome, si legge quanto resta da incassare."),
      h2("Dove finiscono le fatture saldate"),
      t("Quando una fattura è saldata per intero (in un colpo solo o completando gli acconti), il suo PDF timbrato viene spostato automaticamente nella cartella unica dati\\SALDATE, rinominato con il nome del cliente davanti (per esempio “ROSSI SRL - FT 12 del 05-07-2026.pdf”): da lì si possono stampare tutte insieme. Se il pagamento viene annullato, il PDF torna da solo nella cartella del cliente con il nome di prima."),

      h1("5. Tenere d’occhio le scadenze"),
      t("La pagina “Riepilogo” (quella iniziale) mostra: il totale dei crediti aperti, quante fatture sono da incassare e — in rosso — le fatture scadute, dalla più in ritardo. Il pulsante “Report PDF” scarica un documento stampabile con la situazione per cliente (fatturato, incassato, da incassare) e l’elenco delle fatture aperte, da girare al titolare o al commercialista."),
      t("La pagina “Clienti” mostra per ogni cliente tre importi sempre aggiornati: Fatturato (le fatture registrate), Incassato (i pagamenti registrati) e Da incassare (quello che resta aperto, in rosso). Se un cliente risulta aver pagato più del fatturato, accanto compare il credito."),
      h2("Scheda del singolo cliente (da inviare a chi non paga)"),
      t("Nella pagina “Clienti”, in alto, c’è il riquadro “Scheda cliente”: si sceglie il cliente dalla tendina e si preme “Apri scheda” (oppure si clicca sul nome del cliente nella tabella, o sul pulsante “Scheda” a fine riga). Si apre una pagina dedicata SOLO a quel cliente con:"),
      punto("i suoi dati (Partita IVA, codice fiscale, cartella dei documenti);"),
      punto("i riquadri con numero di fatture, fatturato, incassato, da incassare (in rosso) e fatture scadute;"),
      punto("l’elenco di tutte le sue fatture con data, scadenza, giorni di ritardo, stato, totale, pagato e residuo (con ricerca e filtri per stato e anno);"),
      punto("i pagamenti ricevuti."),
      t("Il pulsante “Scarica scheda PDF” produce un documento con l’intestazione dello studio, i dati del cliente, il riepilogo, le fatture aperte con i giorni di ritardo, le fatture saldate e i pagamenti: è pronto da allegare a una mail o da stampare per il cliente insolvente. Il PDF viene scaricato dal browser e resta anche nella cartella dati\\SCHEDE CLIENTI (nome: “codice - cliente - scheda gg-mm-aaaa.pdf”)."),
      t("Dalla scheda si arriva con un clic anche a “Modifica anagrafica” e a “Registra pagamento”.", { italics: true }),

      h1("6. Correggere gli errori"),
      punto("“Tutte le fatture” → “Modifica”: cambia numero, date o importo di una fattura (i conti si aggiustano da soli)."),
      punto("“Tutte le fatture” → “Elimina”: toglie una fattura registrata per sbaglio (il PDF resta nella cartella del cliente). Se sulla fattura ci sono pagamenti registrati, l’app rifiuta l’eliminazione: annullare prima quei pagamenti dalla pagina “Pagamenti”. In alternativa: togliere il PDF dalla cartella del cliente e premere “Analizza” (capitolo 3), che annulla anche i pagamenti collegati."),
      punto("“Pagamenti” → “Annulla”: cancella un incasso registrato male, ripristina i residui e toglie il timbro dal PDF."),
      punto("Una fattura già registrata (stesso cliente, numero e data) rimessa nella INBOX viene rifiutata con “Già registrata”: non si creano doppioni per sbaglio."),
      punto("“Clienti”: aggiungere un cliente nuovo o correggere ragione sociale, P.IVA e codice fiscale."),

      h1("7. Regole d’oro"),
      punto("Registrazioni (analisi fatture, pagamenti): UNA postazione alla volta. Se un collega sta registrando, l’app avvisa che l’Excel è occupato e non rovina nulla: aspettare e ripremere il pulsante."),
      punto("Non tenere aperto il file Excel (dati\\gestione_pagamenti_clienti.xlsx) mentre si usa l’app: se è aperto, l’app si ferma e avvisa senza rovinare nulla. Chiuderlo e ripremere il pulsante."),
      punto("L’Excel si può aprire liberamente per consultare i dati: basta chiuderlo prima di registrare qualcosa."),
      punto("Prima di ogni registrazione l’app salva una copia di sicurezza in dati\\BACKUP (tiene le ultime 30). Per tornare indietro: chiudere l’app, copiare il backup desiderato al posto del file principale."),
      punto("Non rinominare o spostare le cartelle dentro “dati”: le usa il programma."),

      h1("8. Problemi comuni"),
      new Table({ width: { size: 9026, type: WidthType.DXA }, columnWidths: [2800, 6226], rows: [
        rigaTab(["Problema", "Soluzione"], true),
        rigaTab(["Il browser non si apre", "Aprire il browser a mano e digitare nella barra degli indirizzi: 127.0.0.1:8770"]),
        rigaTab(["“Il file Excel è aperto…”", "Chiudere Excel e ripremere il pulsante nell’app."]),
        rigaTab(["“Nessun testo estraibile” su un PDF", "Il PDF è una scansione (immagine): registrare la fattura a mano oppure procurarsi il PDF originale."]),
        rigaTab(["“La cartella dati non è raggiungibile”", "Succede solo con i dati in rete (percorso_dati.txt). L’app riprova da sola 3 volte e poi aspetta: controllare che il PC sia in rete e che la cartella condivisa si apra in Esplora file (se chiede nome utente e password, inserirli e spuntare “Memorizza credenziali”), controllare il percorso scritto in percorso_dati.txt, poi tornare nella finestra nera e premere INVIO."]),
        rigaTab(["“L’app è già aperta su questo PC”", "Non è un errore: il programma era già acceso e si riapre solo il browser. Chiudere l’eventuale finestra nera doppia."]),
      ] }),
      t(""),
      t("Per tutto il resto: contattare chi ha installato il programma.", { italics: true }),
    ],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(require("path").join(__dirname, "docs", "GUIDA SCADENZIARIO.docx"), b);
  console.log("guida creata");
});
