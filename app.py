# SCADENZIARIO — applicazione web locale per la gestione fatture e incassi
import secrets
from datetime import datetime
from functools import wraps

from flask import (Flask, request, redirect, session, flash,
                   render_template, send_file)
from jinja2 import DictLoader

import motore
from pagine import PAGINE, ICONE, TITOLI

# il font è servito dall'app stessa (nessun accesso a internet)
app = Flask(__name__, static_folder=str(motore.RISORSE), static_url_path="/risorse")
app.secret_key = secrets.token_hex(16)
app.jinja_loader = DictLoader(PAGINE)
# i template non hanno estensione .html: Flask non attiverebbe da solo l'escape dei dati
# (nomi clienti, note, nomi file con < > & finirebbero grezzi nella pagina)
app.jinja_env.autoescape = True
app.jinja_env.filters["euro"] = motore.euro
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024   # PDF caricati dal modulo "Nuova fattura"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 7 * 24 * 3600


def ordina_clienti(clienti):
    """Anagrafica in ordine alfabetico (ragione sociale + nome), non nell'ordine dell'Excel."""
    return sorted(clienti, key=lambda c: motore.chiave_nome(f"{c['ragione_sociale']} {c['nome'] or ''}"))


def anni_di(righe, campo):
    """Anni presenti in una lista di righe (dal campo data), dal più recente."""
    anni = set()
    for r in righe:
        v = r.get(campo)
        if isinstance(v, datetime):
            anni.add(str(v.year))
        elif v:
            anni.add(str(v)[-4:])
    return sorted(anni, reverse=True)


def protetta(f):
    """Versione senza password: tutte le pagine sono sempre accessibili (l'app ascolta
    solo su 127.0.0.1, cioè dal PC stesso). Il decoratore resta per non toccare le rotte."""
    return f


@app.context_processor
def variabili_globali():
    try:
        nome_studio = motore.dati_studio()["nome"]
    except Exception:
        nome_studio = ""
    return {"sessione_attiva": True, "icone": ICONE, "titoli": TITOLI,
            "nome_studio": nome_studio}


@app.route("/login")
@app.route("/esci")
def login():
    # vecchi collegamenti alla pagina di accesso: si va direttamente al Riepilogo
    return redirect("/")


@app.route("/")
@protetta
def dashboard():
    d = motore.riepilogo()
    return render_template("dashboard", pagina="dashboard",
                           tot_aperto=motore.euro(d["tot_aperto"]),
                           n_aperte=d["n_aperte"], n_clienti=d["n_clienti"],
                           scadute=d["scadute"], aperte=d["aperte"],
                           grafico=motore.grafico_mensile(d["andamento"]),
                           anni=anni_di(d["aperte"], "data"))


# ---------------- SMISTAMENTO ----------------

@app.route("/smistamento")
@protetta
def smistamento():
    return render_template("smistamento", pagina="smistamento",
                           n_file=len(motore.lista_inbox()), analisi=None, pronte=0)


@app.route("/smistamento/analizza", methods=["POST"])
@protetta
def smistamento_analizza():
    # analisi completa: INBOX (nuove), cartelle CLIENTI (PDF tolti -> fatture da eliminare),
    # PDF non registrati (solo segnalati). Non registra nulla: serve la conferma.
    an = motore.analizza_tutto()
    if an["avviso"]:
        flash(an["avviso"], "errore")
    if not an["esiti"] and not an["mancanti"] and not an["orfani"] and not an["cartelle_mancanti"]:
        flash("Tutto allineato: nessun PDF nuovo nella INBOX e nessuna fattura tolta dalle cartelle.", "ok")
    return render_template("smistamento", pagina="smistamento",
                           n_file=len(motore.lista_inbox()), analisi=an,
                           pronte=sum(1 for e in an["esiti"] if e["ok"]))


@app.route("/smistamento/conferma", methods=["POST"])
@protetta
def smistamento_conferma():
    ok, messaggi = motore.sincronizza()
    for m in messaggi:
        flash(m, "ok" if ok and not m.startswith("NON ELABORATA") else "errore")
    return redirect("/smistamento" if not ok else "/")


# ---------------- PAGAMENTI ----------------

@app.route("/pagamenti")
@protetta
def pagamenti():
    wb = motore.apri_excel()
    clienti = ordina_clienti(motore.leggi_anagrafica(wb))
    nomi = {c["codice"]: c["ragione_sociale"] for c in clienti}
    # per cliente in ordine alfabetico, poi dal pagamento più recente
    acconti = sorted(motore.leggi_acconti(wb),
                     key=lambda a: (motore.chiave_nome(nomi.get(a["codice"], "")),
                                    -(a["data"] or datetime.min).timestamp()))
    situazione = motore.situazione_clienti(wb, acconti=acconti)
    return render_template("pagamenti", pagina="pagamenti",
                           clienti=clienti, acconti=acconti, nomi=nomi,
                           situazione=situazione, anni=anni_di(acconti, "data"))


@app.route("/pagamenti/registra", methods=["POST"])
@protetta
def pagamenti_registra():
    fattura = request.form.get("fattura", "").strip()
    fattura = fattura.removeprefix("FT ").strip() or None
    ok, messaggi = motore.registra_pagamento(
        request.form["codice"], request.form["importo"],
        request.form.get("data", "").strip() or None,
        fattura, request.form.get("modalita") or None)
    for m in messaggi:
        flash(m, "ok" if ok else "errore")
    return redirect("/pagamenti")


@app.route("/pagamenti/elimina/<int:riga>", methods=["POST"])
@protetta
def pagamenti_elimina(riga):
    ok, msg = motore.elimina_pagamento(riga)
    flash(msg, "ok" if ok else "errore")
    return redirect("/pagamenti")


# ---------------- FATTURE ----------------

@app.route("/fatture")
@protetta
def fatture():
    tutte = motore.leggi_fatture(motore.apri_excel())
    tutte.sort(key=lambda f: (motore.chiave_nome(f["cliente"]), motore._parse_data(f["data"]) or datetime.max, f["riga"]))
    return render_template("fatture", pagina="fatture", fatture=tutte, anni=anni_di(tutte, "data"))


@app.route("/fatture/nuova", methods=["GET", "POST"])
@protetta
def fattura_nuova():
    clienti = ordina_clienti(motore.leggi_anagrafica(motore.apri_excel()))
    if request.method == "POST":
        codice = request.form.get("codice", "").strip()
        file = request.files.get("pdf")
        pdf_bytes = file.read() if (file and file.filename) else None
        nuovo = {k: request.form.get("nuovo_" + k, "") for k in ("ragione_sociale", "nome", "piva", "cf")}
        ok, msg = motore.registra_fattura_manuale(
            None if codice in ("", "nuovo") else int(codice), nuovo,
            request.form.get("numero", ""), request.form.get("data", "").strip(),
            request.form.get("scadenza", "").strip(), request.form.get("totale", ""), pdf_bytes)
        flash(msg, "ok" if ok else "errore")
        if ok:
            return redirect("/fatture")
        return render_template("fattura_nuova", pagina="fatture", clienti=clienti,
                               v=request.form, oggi=datetime.now().strftime("%d/%m/%Y"))
    return render_template("fattura_nuova", pagina="fatture", clienti=clienti, v={},
                           oggi=datetime.now().strftime("%d/%m/%Y"))


@app.route("/fatture/modifica/<int:riga>", methods=["GET", "POST"])
@protetta
def fattura_modifica(riga):
    if request.method == "POST":
        ok, msg = motore.modifica_fattura(
            riga, request.form["numero"].strip(), request.form["data"].strip(),
            request.form.get("scadenza", "").strip(), request.form["totale"])
        flash(msg, "ok" if ok else "errore")
        return redirect("/fatture" if ok else f"/fatture/modifica/{riga}")
    f = next((x for x in motore.leggi_fatture(motore.apri_excel())
              if x["riga"] == riga), None)
    if f is None:
        flash("Fattura non trovata.", "errore")
        return redirect("/fatture")
    return render_template("fattura_modifica", pagina="fatture", f=f)


@app.route("/fatture/elimina/<int:riga>", methods=["POST"])
@protetta
def fattura_elimina(riga):
    ok, msg = motore.elimina_fattura(riga)
    flash(msg, "ok" if ok else "errore")
    return redirect("/fatture")


# ---------------- CLIENTI ----------------

@app.route("/clienti")
@protetta
def clienti():
    wb = motore.apri_excel()
    tutti = ordina_clienti(motore.leggi_anagrafica(wb))
    situazione = motore.situazione_clienti(wb)
    codice_mod = request.args.get("modifica", type=int)
    in_modifica = next((c for c in tutti if c["codice"] == codice_mod), None)
    tot_da_incassare = sum(v["da_incassare"] for v in situazione.values())
    return render_template("clienti", pagina="clienti",
                           clienti=tutti, in_modifica=in_modifica,
                           situazione=situazione, tot_da_incassare=tot_da_incassare)


@app.route("/clienti/salva", methods=["POST"])
@protetta
def clienti_salva():
    codice = request.form.get("codice", "").strip() or None
    ok, msg = motore.salva_cliente(
        int(codice) if codice else None,
        request.form["ragione_sociale"], request.form.get("nome"),
        request.form.get("piva"), request.form.get("cf"), request.form.get("note"))
    flash(msg, "ok" if ok else "errore")
    return redirect("/clienti")


@app.route("/clienti/<int:codice>")
@protetta
def scheda_cliente(codice):
    """Scheda del singolo cliente: anagrafica, tutte le sue fatture, i pagamenti e i totali."""
    sc = motore.scheda_cliente(codice)
    if sc is None:
        flash(f"Cliente {codice} non trovato.", "errore")
        return redirect("/clienti")
    return render_template("scheda_cliente", pagina="scheda", sc=sc, c=sc["cliente"],
                           cartella=motore.nome_cartella_cliente(sc["cliente"]),
                           anni=anni_di(sc["fatture"], "data"))


@app.route("/clienti/<int:codice>/pdf")
@protetta
def scheda_cliente_pdf(codice):
    """PDF della scheda cliente, salvato in dati\\SCHEDE CLIENTI e scaricato dal browser."""
    percorso, sc = motore.genera_scheda_cliente_pdf(codice)
    if percorso is None:
        flash(f"Cliente {codice} non trovato.", "errore")
        return redirect("/clienti")
    return send_file(percorso, as_attachment=True, download_name=percorso.name)


# ---------------- REPORT ----------------

@app.route("/impostazioni", methods=["GET", "POST"])
@protetta
def impostazioni():
    if request.method == "POST":
        motore.salva_impostazioni(request.form)
        flash("Impostazioni salvate.", "ok")
        return redirect("/impostazioni")
    return render_template("impostazioni", pagina="impostazioni",
                           studio=motore.dati_studio(), cartella_dati=motore.DATI)


@app.route("/report")
@protetta
def report():
    percorso = motore.DATI / f"Report crediti {datetime.now():%d-%m-%Y}.pdf"
    motore.genera_report_pdf(percorso)
    return send_file(percorso, as_attachment=True)


def trova_cartella_dati():
    """Cartella dati: "dati" accanto all'app (creata vuota al primo avvio) oppure quella
    indicata in percorso_dati.txt (es. una cartella condivisa in rete). Se non è
    raggiungibile spiega cosa fare e permette di riprovare con INVIO invece di chiudersi."""
    import time
    while True:
        for tentativo in range(3):
            trovata = motore.cerca_dati()
            if trovata is not None:
                return trovata
            print(f"Cerco la cartella dati... (tentativo {tentativo + 1} di 3)")
            time.sleep(3)
        print()
        print("ERRORE: la cartella dati non è raggiungibile:")
        print(f"  {motore._percorso_dati()}")
        print("Cosa controllare:")
        print("  1. Se la cartella è in rete: il PC è collegato e il NAS/PC che la condivide è acceso?")
        print("     Aprire la cartella in Esplora file (se chiede le credenziali, spuntare 'Memorizza credenziali').")
        print("  2. Il percorso scritto in percorso_dati.txt (accanto all'app) è giusto?")
        print("     Per tornare ai dati su questo PC basta eliminare o svuotare percorso_dati.txt.")
        print("  3. Sistemato il problema, tornare qui e premere INVIO.")
        print()
        risposta = input("Premere INVIO per riprovare, oppure scrivere X e INVIO per chiudere: ")
        if risposta.strip().lower() == "x":
            return None


def avvia():
    import socket
    import threading
    import webbrowser
    cartella = trova_cartella_dati()
    if cartella is None:
        return
    motore.imposta_dati(cartella)
    porta = motore.carica_config()["porta"]
    url = f"http://127.0.0.1:{porta}"
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", porta)) == 0:
            print("L'app è già aperta su questo PC: apro il browser.")
            webbrowser.open(url)
            return
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"SCADENZIARIO avviato: {url}")
    print(f"Cartella dati: {motore.DATI}")
    print("Lasciare questa finestra aperta. Per chiudere l'app: chiudere questa finestra.")
    app.run(host="127.0.0.1", port=porta, debug=False)


if __name__ == "__main__":
    avvia()
