# SCADENZIARIO — motore: lettura/scrittura Excel, analisi PDF fatture,
# pagamenti, timbri, backup. Autonomo: non dipende dagli script esterni.
import io
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pdfplumber
from openpyxl import load_workbook
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from xml.sax.saxutils import escape

# --- percorsi: di norma i dati stanno nella cartella "dati" accanto all'exe (o allo script).
#     Un file "percorso_dati.txt" accanto all'exe può indicare una cartella diversa, ad esempio
#     una cartella condivisa in rete comune a più PC (es. \\NAS\Condivisa\SCADENZIARIO\dati). ---
if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
DATI_LOCALI = BASE / "dati"

NOME_EXCEL = "gestione_pagamenti_clienti.xlsx"
PORTA_INIZIALE = 8770   # porta locale del browser (modificabile nel config.json dei dati)

# risorse incluse nel pacchetto (font, modello Excel vuoto): nell'exe stanno in _internal\risorse
RISORSE = (Path(getattr(sys, "_MEIPASS", BASE)) / "risorse") if getattr(sys, "frozen", False) else BASE / "risorse"

# intestazione dello studio (report PDF): vuota, si compila dalla pagina "Impostazioni"
# (salvata nella voce "studio" di config.json)
STUDIO = {
    "nome": "",
    "piva": "",
    "cf": "",
    "indirizzo": "",
    "telefono": "",
    "email": "",
    # testo che nelle fatture PDF precede il nome del cliente (se vuoto: il nome dello studio)
    "intestazione_fatture": "",
}


def _percorso_override():
    """Percorso indicato in percorso_dati.txt (None se il file manca o è vuoto)."""
    override = BASE / "percorso_dati.txt"
    if override.exists():
        testo = override.read_text(encoding="utf-8-sig").strip()
        if testo:
            p = Path(testo)
            return p if p.is_absolute() else BASE / p
    return None


def _percorso_dati():
    return _percorso_override() or DATI_LOCALI


def raggiungibile(percorso):
    """True se nella cartella indicata c'è l'Excel dei dati (senza sollevare errori di rete)."""
    try:
        return (Path(percorso) / NOME_EXCEL).exists()
    except OSError:
        return False


CARTELLE_DATI = ("INBOX", "CLIENTI", "SALDATE", "BACKUP", "ORIGINALI", "SCHEDE CLIENTI")


def inizializza_dati(percorso):
    """Al primo avvio crea una cartella dati vuota (Excel dal modello, sottocartelle,
    config di base) se lì non c'è ancora l'Excel. La cartella madre deve esistere:
    per un percorso di rete, la condivisione deve essere raggiungibile."""
    percorso = Path(percorso)
    try:
        if (percorso / NOME_EXCEL).exists() or not percorso.parent.exists():
            return
        percorso.mkdir(exist_ok=True)
        shutil.copy(RISORSE / "modello_vuoto.xlsx", percorso / NOME_EXCEL)
        for nome in CARTELLE_DATI:
            (percorso / nome).mkdir(exist_ok=True)
        if not (percorso / "config.json").exists():
            (percorso / "config.json").write_text(json.dumps(
                {"porta": PORTA_INIZIALE}, indent=2), encoding="utf-8")
    except OSError:
        pass


def cerca_dati():
    """Cartella dati da usare: quella di percorso_dati.txt se presente, altrimenti "dati"
    accanto all'app; al primo avvio viene creata vuota. Ritorna None se non raggiungibile."""
    percorso = _percorso_dati()
    inizializza_dati(percorso)
    return percorso if raggiungibile(percorso) else None


def imposta_dati(percorso):
    """Imposta la cartella dati (e tutte le sottocartelle) usata dal motore."""
    global DATI, EXCEL, INBOX, CARTELLA_CLIENTI, SALDATE, BACKUP, CONFIG, ORIGINALI, SCHEDE
    DATI = Path(percorso)
    EXCEL = DATI / NOME_EXCEL
    INBOX = DATI / "INBOX"
    CARTELLA_CLIENTI = DATI / "CLIENTI"
    SALDATE = DATI / "SALDATE"
    BACKUP = DATI / "BACKUP"
    CONFIG = DATI / "config.json"
    # copie pulite dei PDF prima del primo timbro: servono per togliere i timbri all'annullo
    ORIGINALI = DATI / "ORIGINALI"
    # schede cliente in PDF (situazione fatture/pagamenti da inviare al cliente)
    SCHEDE = DATI / "SCHEDE CLIENTI"


imposta_dati(_percorso_dati())

RIGA_DATI = 5
# Insoluti e Acconti: righe utili 5..5000 (con ~100 fatture a trimestre le vecchie 500 righe
# sarebbero finite in circa un anno). Le formule del foglio Clienti vengono riallineate a ogni salvataggio.
ULTIMA_RIGA_REGISTRI = 5000
ULTIMA_RIGA_CLIENTI = 1000
MAX_BACKUP = 30

CARATTERI_VIETATI = r'<>:"/\\|?*'


# ============================ CONFIGURAZIONE ============================

def carica_config():
    cfg = {"porta": PORTA_INIZIALE, "piva_studio": None, "cf_studio": None}
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    return cfg


def dati_studio():
    """Intestazione dello studio: valori vuoti eventualmente compilati in config.json."""
    d = dict(STUDIO)
    d.update(carica_config().get("studio") or {})
    return {k: str(v or "").strip() for k, v in d.items()}


def salva_impostazioni(studio):
    """Salva i dati dello studio (pagina Impostazioni). P.IVA e CF dello studio servono
    anche all'analisi dei PDF, per distinguerli da quelli del cliente."""
    cfg = carica_config()
    pulito = {k: str(studio.get(k) or "").strip() for k in STUDIO}
    pulito["piva"] = normalizza_piva(pulito["piva"]) if pulito["piva"] else ""
    pulito["cf"] = pulito["cf"].upper()
    cfg["studio"] = pulito
    cfg["piva_studio"] = pulito["piva"] or None
    cfg["cf_studio"] = pulito["cf"] or None
    salva_config(cfg)


def salva_config(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================ UTILITÀ ============================

def sanifica_nome(nome):
    nome = unicodedata.normalize("NFKC", str(nome))
    nome = "".join(c for c in nome if c not in CARATTERI_VIETATI)
    return re.sub(r"\s+", " ", nome).strip().rstrip(".")


def normalizza_piva(piva):
    s = re.sub(r"\D", "", str(piva or ""))
    return s.zfill(11) if s else ""


def euro(v):
    s = f"{float(v):,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_importo_it(s):
    s = str(s).strip().replace("€", "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)


def trimestre(data):
    romani = {1: "I", 2: "II", 3: "III", 4: "IV"}
    return f"{romani[(data.month - 1) // 3 + 1]} TRIM {data.year}"


def excel_scrivibile():
    """True se il file Excel non è bloccato da un altro programma."""
    try:
        with open(EXCEL, "r+b"):
            return True
    except PermissionError:
        return False


def fai_backup():
    """Copia l'Excel in BACKUP con data e ora; tiene solo le ultime MAX_BACKUP."""
    BACKUP.mkdir(exist_ok=True)
    dest = BACKUP / f"backup_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    shutil.copy(EXCEL, dest)
    vecchi = sorted(BACKUP.glob("backup_*.xlsx"))
    for f in vecchi[:-MAX_BACKUP]:
        f.unlink()


def apri_excel():
    return load_workbook(EXCEL)


def salva_excel(wb):
    """Unico punto di salvataggio: riallinea le formule del foglio Clienti (i registri
    possono crescere oltre le 500 righe originali) e scrive il file."""
    aggiorna_formule_clienti(wb)
    wb.save(EXCEL)


def _come_codice(v):
    """Codice cliente come intero; None se la cella è vuota o non numerica
    (una riga scritta a mano male nell'Excel non deve bloccare tutta l'app)."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _come_data(v):
    """Data da una cella Excel: datetime così com'è, testo gg/mm/aaaa convertito,
    altrimenti None."""
    if isinstance(v, datetime):
        return v
    if v is None or v == "":
        return None
    if hasattr(v, "year") and not isinstance(v, datetime):   # datetime.date
        return datetime(v.year, v.month, v.day)
    return _parse_data(v)


# ============================ ANAGRAFICA ============================

def leggi_anagrafica(wb):
    ws = wb["Clienti"]
    clienti = []
    for r in range(RIGA_DATI, ws.max_row + 1):
        codice = _come_codice(ws.cell(row=r, column=1).value)
        if codice is None:
            continue
        clienti.append({
            "codice": codice, "riga": r,
            "ragione_sociale": ws.cell(row=r, column=2).value or "",
            "nome": ws.cell(row=r, column=3).value,
            "piva": normalizza_piva(ws.cell(row=r, column=4).value),
            "cf": str(ws.cell(row=r, column=5).value or "").strip(),
            "dovuto": ws.cell(row=r, column=6).value or 0,
            "note": ws.cell(row=r, column=13).value or "",
        })
    return clienti


def nome_cartella_cliente(c):
    rs = str(c["ragione_sociale"]).strip()
    if c.get("nome"):
        rs = f"{rs} {str(c['nome']).strip()}"
    return f"{c['codice']} - {sanifica_nome(rs)}"


def cartella_di(c):
    return CARTELLA_CLIENTI / nome_cartella_cliente(c)


def formule_riga_clienti(ws, r):
    u = ULTIMA_RIGA_REGISTRI
    ws.cell(row=r, column=10).value = (
        f'=IF($A{r}="","",SUMIF(Acconti!$B$5:$B${u},$A{r},Acconti!$D$5:$D${u}))')
    ws.cell(row=r, column=11).value = (
        f'=IF($A{r}="","",SUMIF(Insoluti!$A$5:$A${u},$A{r},Insoluti!$E$5:$E${u}))')
    ws.cell(row=r, column=12).value = f'=IF($A{r}="","",F{r}-IF(J{r}="",0,J{r}))'


def aggiorna_formule_clienti(wb):
    """Riscrive le formule J/K/L di tutte le righe cliente con l'intervallo attuale dei registri."""
    ws = wb["Clienti"]
    for r in range(RIGA_DATI, ULTIMA_RIGA_CLIENTI + 1):
        if ws.cell(row=r, column=1).value not in (None, ""):
            formule_riga_clienti(ws, r)


def crea_cliente(wb, clienti, ragione_sociale, nome=None, piva="", cf=""):
    """Aggiunge un cliente nuovo al foglio Clienti (senza salvare il file) e lo
    accoda alla lista `clienti`. Ritorna il dict del cliente, o None se l'anagrafica è piena."""
    ws = wb["Clienti"]
    riga = next((r for r in range(RIGA_DATI, ULTIMA_RIGA_CLIENTI + 1)
                 if ws.cell(row=r, column=1).value in (None, "")), None)
    if riga is None:
        return None
    codice = max((c["codice"] for c in clienti), default=0) + 1
    ws.cell(row=riga, column=1).value = codice
    ws.cell(row=riga, column=2).value = str(ragione_sociale).strip().upper()
    ws.cell(row=riga, column=3).value = (nome or "").strip().upper() or None
    ws.cell(row=riga, column=4).value = normalizza_piva(piva) or None
    ws.cell(row=riga, column=5).value = str(cf or "").strip().upper() or None
    formule_riga_clienti(ws, riga)
    cliente = {"codice": codice, "riga": riga,
               "ragione_sociale": str(ragione_sociale).strip().upper(),
               "nome": (nome or "").strip().upper() or None,
               "piva": normalizza_piva(piva), "cf": str(cf or "").strip().upper(),
               "dovuto": 0, "note": ""}
    clienti.append(cliente)
    return cliente


def cliente_esistente(clienti, piva, cf):
    """Cliente già in anagrafica con la stessa P.IVA o lo stesso CF (None se nessuno)."""
    piva = normalizza_piva(piva)
    cf = str(cf or "").strip().upper()
    return next((c for c in clienti
                 if (piva and c["piva"] == piva) or (cf and c["cf"].upper() == cf)), None)


def chiave_nome(nome):
    """Chiave di ordinamento alfabetico (maiuscole, spazi normalizzati, senza accenti)."""
    s = unicodedata.normalize("NFKD", str(nome or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def cliente_con_nome_simile(clienti, ragione_sociale, nome=None):
    """Cliente esistente il cui nome inizia con quello digitato (o viceversa): serve a bloccare
    le schede create per sbaglio con un nome a metà (es. 'LA BELL' per LA BELLA LAVANDERIA)
    quando non ci sono P.IVA né CF per distinguerli. None se nessuno."""
    digitato = chiave_nome(f"{ragione_sociale} {nome or ''}")
    if len(digitato) < 3:
        return None
    for c in clienti:
        esistente = chiave_nome(f"{c['ragione_sociale']} {c['nome'] or ''}")
        if esistente.startswith(digitato) or digitato.startswith(esistente):
            return c
    return None


def salva_cliente(codice, ragione_sociale, nome, piva, cf, note):
    """Crea o aggiorna un cliente. codice=None -> nuovo. Ritorna (ok, messaggio)."""
    if not excel_scrivibile():
        return False, "Il file Excel è aperto in un altro programma: chiudilo e riprova."
    fai_backup()
    wb = apri_excel()
    ws = wb["Clienti"]
    clienti = leggi_anagrafica(wb)
    if codice is None:
        doppio = cliente_esistente(clienti, piva, cf)
        if doppio:
            return False, (f"Esiste già il cliente {doppio['codice']} - {doppio['ragione_sociale']} "
                           "con questa P.IVA / codice fiscale.")
        if not (normalizza_piva(piva) or str(cf or "").strip()):
            simile = cliente_con_nome_simile(clienti, ragione_sociale, nome)
            if simile:
                return False, (f"Nome troppo simile al cliente esistente {simile['codice']} - {simile['ragione_sociale']}"
                               f"{' ' + simile['nome'] if simile['nome'] else ''}: se è un cliente diverso, "
                               "indicare P.IVA o codice fiscale.")
        nuovo = crea_cliente(wb, clienti, ragione_sociale, nome, piva, cf)
        if nuovo is None:
            return False, "Anagrafica piena: contattare l'assistenza per ampliare il foglio."
        codice, riga = nuovo["codice"], nuovo["riga"]
        vecchia_cartella = None
    else:
        cli = next((c for c in clienti if c["codice"] == int(codice)), None)
        if cli is None:
            return False, f"Cliente {codice} non trovato."
        riga = cli["riga"]
        vecchia_cartella = cartella_di(cli)
    ws.cell(row=riga, column=2).value = ragione_sociale.strip().upper()
    ws.cell(row=riga, column=3).value = (nome or "").strip().upper() or None
    ws.cell(row=riga, column=4).value = str(piva or "").strip()
    ws.cell(row=riga, column=5).value = str(cf or "").strip()
    ws.cell(row=riga, column=13).value = (note or "").strip() or None
    salva_excel(wb)

    wb2 = apri_excel()
    nuovo = next(c for c in leggi_anagrafica(wb2) if c["codice"] == int(codice))
    nuova_cartella = cartella_di(nuovo)
    if vecchia_cartella and vecchia_cartella.exists() and vecchia_cartella != nuova_cartella:
        vecchia_cartella.rename(nuova_cartella)
        vecchi_orig = ORIGINALI / vecchia_cartella.name
        if vecchi_orig.exists():
            vecchi_orig.rename(ORIGINALI / nuova_cartella.name)
    else:
        nuova_cartella.mkdir(parents=True, exist_ok=True)
    return True, f"Cliente {codice} salvato."


def situazione_clienti(wb, fatture=None, acconti=None):
    """Per ogni codice cliente: fatturato (somma fatture registrate), incassato
    (somma pagamenti), da incassare (somma residui aperti), n. fatture aperte,
    eventuale credito (pagato più del fatturato)."""
    fatture = leggi_fatture(wb) if fatture is None else fatture
    acconti = leggi_acconti(wb) if acconti is None else acconti
    sit = {}

    def voce(codice):
        return sit.setdefault(codice, {"fatturato": 0.0, "incassato": 0.0,
                                       "da_incassare": 0.0, "n_aperte": 0, "credito": 0.0})
    for f in fatture:
        v = voce(f["codice"])
        v["fatturato"] = round(v["fatturato"] + f["totale"], 2)
        v["da_incassare"] = round(v["da_incassare"] + f["residuo"], 2)
        if f["residuo"] > 0:
            v["n_aperte"] += 1
    for a in acconti:
        v = voce(a["codice"])
        v["incassato"] = round(v["incassato"] + float(a["importo"] or 0), 2)
    for v in sit.values():
        credito = round(v["incassato"] - (v["fatturato"] - v["da_incassare"]), 2)
        v["credito"] = credito if credito > 0 else 0.0
    return sit


# ============================ FATTURE (INSOLUTI) ============================

def leggi_fatture(wb):
    """Tutte le righe del foglio Insoluti con i dati sciolti dalla nota."""
    ws = wb["Insoluti"]
    clienti = {c["codice"]: c for c in leggi_anagrafica(wb)}
    fatture = []
    for r in range(RIGA_DATI, ULTIMA_RIGA_REGISTRI + 1):
        codice = _come_codice(ws.cell(row=r, column=1).value)
        if codice is None:
            continue
        nota = str(ws.cell(row=r, column=8).value or "")
        residuo = ws.cell(row=r, column=5).value
        residuo = float(residuo) if isinstance(residuo, (int, float)) else 0.0
        scad = _come_data(ws.cell(row=r, column=4).value)
        m_tot = re.search(r"Totale € ([\d.,]+)", nota)
        totale = parse_importo_it(m_tot.group(1)) if m_tot else residuo
        m_num = re.match(r"FT (.+?) del (\d{2}/\d{2}/\d{4})", nota)
        cli = clienti.get(codice)
        ritardo = (datetime.now() - scad).days if (scad and residuo > 0) else None
        fatture.append({
            "riga": r, "codice": codice,
            "cliente": cli["ragione_sociale"] if cli else "?",
            "numero": m_num.group(1) if m_num else "?",
            "data": m_num.group(2) if m_num else "",
            "periodo": ws.cell(row=r, column=3).value or "",
            "scadenza": scad, "residuo": residuo, "totale": totale,
            "stato": "Aperta" if residuo > 0 else "Saldata",
            "ritardo": ritardo if (ritardo and ritardo > 0) else None,
            "nota": nota,
            "file": (re.search(r"file: (.+?\.pdf)", nota, re.I) or [None]).group(1)
                    if re.search(r"file: (.+?\.pdf)", nota, re.I) else None,
        })
    return fatture


def formule_riga_insoluti(ws, r):
    ws.cell(row=r, column=2).value = (
        f'=IF($A{r}="","",IFERROR(INDEX(Clienti!$B:$B,MATCH($A{r},Clienti!$A:$A,0)),"Codice non trovato"))')
    ws.cell(row=r, column=6).value = f'=IF(OR($A{r}="",$D{r}=""),"",TODAY()-$D{r})'
    ws.cell(row=r, column=7).value = f'=IF($A{r}="","",IF($E{r}=0,"Saldato","Aperto"))'


def prima_riga_libera(ws, colonna=1):
    for r in range(RIGA_DATI, ULTIMA_RIGA_REGISTRI + 1):
        if ws.cell(row=r, column=colonna).value in (None, ""):
            return r
    raise RuntimeError("Registro pieno")


def scrivi_fattura(wb, cliente, numero, data, scadenza, totale, nome_file,
                   riga=None, residuo=None):
    """Scrive (o riscrive) una riga fattura nel foglio Insoluti."""
    ws = wb["Insoluti"]
    r = riga or prima_riga_libera(ws)
    ws.cell(row=r, column=1).value = cliente["codice"]
    ws.cell(row=r, column=3).value = trimestre(data)
    cella_scad = ws.cell(row=r, column=4)
    cella_scad.value = scadenza
    if scadenza:
        cella_scad.number_format = "DD/MM/YYYY"
    cella_imp = ws.cell(row=r, column=5)
    cella_imp.value = residuo if residuo is not None else totale
    cella_imp.number_format = '#,##0.00" €"'
    nota = f"FT {numero} del {data:%d/%m/%Y} — Totale € {euro(totale)}"
    if nome_file:
        nota += f" — file: {nome_file}"
    ws.cell(row=r, column=8).value = nota
    formule_riga_insoluti(ws, r)
    return r


def aggiorna_dovuto(wb, codice, delta):
    ws = wb["Clienti"]
    for r in range(RIGA_DATI, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == codice:
            cella = ws.cell(row=r, column=6)
            cella.value = round((cella.value or 0) + delta, 2)
            cella.number_format = '#,##0.00" €"'
            return


def modifica_fattura(riga, numero, data_str, scadenza_str, totale_str):
    """Modifica una fattura esistente; aggiusta residuo e dovuto per differenza."""
    if not excel_scrivibile():
        return False, "Il file Excel è aperto in un altro programma: chiudilo e riprova."
    wb = apri_excel()
    fatture = leggi_fatture(wb)
    f = next((x for x in fatture if x["riga"] == int(riga)), None)
    if f is None:
        return False, "Fattura non trovata."
    try:
        data = datetime.strptime(data_str, "%d/%m/%Y")
        scadenza = datetime.strptime(scadenza_str, "%d/%m/%Y") if scadenza_str else None
        totale = parse_importo_it(totale_str)
    except ValueError:
        return False, "Data o importo non validi (usare gg/mm/aaaa e importi tipo 1.234,56)."
    fai_backup()
    delta = round(totale - f["totale"], 2)
    nuovo_residuo = max(0.0, round(f["residuo"] + delta, 2))
    ws = wb["Insoluti"]
    cliente = {"codice": f["codice"]}
    # conservo eventuali diciture di pagamento in coda alla nota
    coda = ""
    m = re.search(r"((?:; (?:acconto|saldata).*)+)$", f["nota"])
    if m:
        coda = m.group(1)
    # se cambia il numero, i pagamenti collegati devono seguirlo: altrimenti un annullo
    # successivo non ritroverebbe la fattura e il residuo non verrebbe ripristinato
    n_rinumerati = 0
    if numero != f["numero"]:
        n_rinumerati = _rinumera_in_acconti(wb, f, numero)
    scrivi_fattura(wb, cliente, numero, data, scadenza, totale,
                   f["file"], riga=f["riga"], residuo=nuovo_residuo)
    if coda:
        cella = ws.cell(row=f["riga"], column=8)
        cella.value = cella.value + coda
    if delta:
        aggiorna_dovuto(wb, f["codice"], delta)
    salva_excel(wb)
    msg = f"Fattura FT {numero} aggiornata."
    if n_rinumerati:
        msg += f" Aggiornato il numero anche su {n_rinumerati} pagament{'o' if n_rinumerati == 1 else 'i'} collegat{'o' if n_rinumerati == 1 else 'i'}."
    return True, msg


def _rinumera_in_acconti(wb, f, nuovo_numero):
    """Nelle note del foglio Acconti sostituisce 'FT <vecchio numero> ...' con il nuovo numero
    per i soli pagamenti collegati a questa fattura. Ritorna quanti pagamenti ha toccato."""
    wa = wb["Acconti"]
    n = 0
    for acc in pagamenti_collegati(f, leggi_acconti(wb)):
        vecchio, nuovo = f"FT {f['numero']} ", f"FT {nuovo_numero} "
        nota = acc["nota"]
        # sostituisco solo la voce di questa fattura (potrebbero esserci fatture omonime)
        data_str = f"{acc['data']:%d/%m/%Y}" if acc["data"] else ""
        pezzi = nota.split(", ")
        for i, pezzo in enumerate(pezzi):
            m = RE_QUOTE_ACCONTO.fullmatch(pezzo.strip())
            if not m or m.group(1) != f["numero"]:
                continue
            _, dicitura = _dicitura_quota(m.group(2), m.group(3), data_str)
            if dicitura in f["nota"]:
                pezzi[i] = pezzo.replace(vecchio, nuovo, 1)
                break
        wa.cell(row=acc["riga"], column=7).value = ", ".join(pezzi)
        n += 1
    return n


def elimina_fattura(riga):
    """Elimina una fattura: toglie la riga e sottrae il totale dal dovuto."""
    if not excel_scrivibile():
        return False, "Il file Excel è aperto in un altro programma: chiudilo e riprova."
    wb = apri_excel()
    f = next((x for x in leggi_fatture(wb) if x["riga"] == int(riga)), None)
    if f is None:
        return False, "Fattura non trovata."
    collegati = pagamenti_collegati(f, leggi_acconti(wb))
    if collegati:
        # eliminarla lascerebbe pagamenti "orfani" non più annullabili
        elenco = ", ".join(f"€ {euro(a['importo'])} del {a['data']:%d/%m/%Y}" if a["data"]
                           else f"€ {euro(a['importo'])}" for a in collegati)
        return False, (f"FT {f['numero']} ha pagamenti collegati ({elenco}): annullarli prima "
                       "dalla pagina Pagamenti, poi eliminare la fattura.")
    fai_backup()
    _elimina_riga_fattura(wb, f)
    salva_excel(wb)
    return True, f"Fattura FT {f['numero']} eliminata (il PDF resta nella cartella del cliente)."


def _elimina_riga_fattura(wb, f):
    """Svuota la riga della fattura nel foglio Insoluti e sottrae il totale dal fatturato
    del cliente (parte comune di elimina_fattura e della sincronizzazione)."""
    ws = wb["Insoluti"]
    for col in (1, 3, 4, 5, 8):
        ws.cell(row=f["riga"], column=col).value = None
    formule_riga_insoluti(ws, f["riga"])
    aggiorna_dovuto(wb, f["codice"], -f["totale"])


# ============================ ANALISI PDF ============================

RE_PIVA = re.compile(r"\b(?:IT\s*)?(\d{11})\b")
RE_CF = re.compile(r"\b([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])\b")
RE_IMPORTO = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")

PATTERN_NUMERO = [
    re.compile(r"\bnr\.?\s+([A-Z]{0,6}\s?\d+(?:[/\-]\d+)*(?:[/\-][A-Z0-9]+)?)\s+del\s", re.I),
    re.compile(r"Numero\s+(?:documento|fattura)\s*[:\s]+([A-Z0-9][\w/\-\.]*)", re.I),
    re.compile(r"Fattura\s*(?:n(?:r)?\.?|num(?:ero)?\.?)\s*[:\s]*([A-Z0-9][\w/\-\.]*)", re.I),
]
PATTERN_TOTALE = [
    re.compile(r"(?:Importo\s+totale\s+documento|Totale\s+documento|Totale\s+fattura)\D{0,20}?" + RE_IMPORTO.pattern, re.I),
    re.compile(r"Netto\s+a\s+pagare\D{0,20}?" + RE_IMPORTO.pattern, re.I),
]
PATTERN_SCADENZA = [
    re.compile(r"(?:Data\s+)?scadenz\w*(?:\s+pagamento)?\s*[:\s]*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})", re.I),
    re.compile(r"DATA\s+SCADENZA.{0,250}?(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})", re.I | re.S),
]
PATTERN_DATA_DOC = [
    re.compile(r"\bnr\.?\s+.{1,30}?\bdel\s+(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})", re.I),
    re.compile(r"Data\s+(?:documento|fattura|emissione)\s*[:\s]*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})", re.I),
]
RE_DATA = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")


def _parse_data(testo):
    m = RE_DATA.search(str(testo))
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _re_intestazione():
    """Riga della fattura con il nome dello studio seguito da quello del cliente: usa
    "intestazione_fatture" delle Impostazioni o, se vuoto, il nome dello studio."""
    studio = dati_studio()
    testo = studio["intestazione_fatture"] or studio["nome"]
    if not testo:
        return None
    parole = [re.escape(p) for p in testo.upper().split()]
    return re.compile(r"\s+".join(parole) + r"[ \t]+(.+)", re.I)
RE_RIGA_NON_NOME = re.compile(
    r"(?i)^(P\.?\s?IVA|C\.?\s?F\.?|VIA\b|PIAZZA\b|CORSO\b|VICO\b|LARGO\b|VIALE\b|\d|Codice|Telefono|Data|FORNITORE|PRODOTTI)")


def estrai_ragione_sociale(testo):
    """Nome del cliente dalla riga d'intestazione della fattura (accanto al nome dello studio),
    con l'eventuale seguito sulla riga successiva (ragioni sociali lunghe andate a capo)."""
    regola = _re_intestazione()
    if regola is None:
        return None
    righe = testo.splitlines()
    for i, r in enumerate(righe):
        m = regola.search(r)
        if not m:
            continue
        nome = m.group(1).strip(" :;")
        if i + 1 < len(righe):
            seguito = righe[i + 1].strip()
            if seguito and seguito == seguito.upper() and not RE_RIGA_NON_NOME.match(seguito):
                nome = f"{nome} {seguito}"
        nome = re.sub(r"\s+", " ", nome).strip()
        if nome and not re.fullmatch(r"[\d\s.,/-]+", nome):
            return nome[:80]
    return None


def analizza_pdf(percorso, clienti, cfg):
    """Analizza un PDF fattura. Ritorna un dict con esito e dati estratti."""
    esito = {"file": percorso.name, "ok": False, "errore": None, "cliente": None,
             "nuovo_cliente": None, "numero": None, "data": None,
             "scadenza": None, "totale": None}
    try:
        with pdfplumber.open(percorso) as pdf:
            testo = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        esito["errore"] = f"PDF illeggibile: {e}"
        return esito
    if not testo.strip():
        esito["errore"] = "Nessun testo estraibile (PDF scansionato?)"
        return esito

    pive = []
    for m in RE_PIVA.finditer(testo):
        if m.group(1) not in pive:
            pive.append(m.group(1))
    cfs = list(dict.fromkeys(RE_CF.findall(testo.upper())))   # CF di persone fisiche, in ordine
    match = [c for c in clienti if c["piva"] and c["piva"] in pive]
    if not match:
        match = [c for c in clienti if c["cf"] and c["cf"].upper() in cfs]
    if len(match) > 1:
        esito["errore"] = f"Più clienti corrispondono ({', '.join(str(c['codice']) for c in match)})"
        return esito
    if len(match) == 1:
        esito["cliente"] = match[0]
        # imparo P.IVA e CF dello studio dalla prima fattura di un cliente conosciuto
        altre = [p for p in pive if p != match[0]["piva"]]
        if cfg.get("piva_studio") is None and len(altre) == 1:
            cfg["piva_studio"] = altre[0]
            salva_config(cfg)
        altri_cf = [c for c in cfs if c != match[0]["cf"].upper()]
        if cfg.get("cf_studio") is None and len(altri_cf) == 1:
            cfg["cf_studio"] = altri_cf[0]
            salva_config(cfg)
    else:
        # cliente nuovo: P.IVA diversa da quella dello studio, oppure (persona fisica) solo il CF
        candidate = [p for p in pive if p != cfg.get("piva_studio")]
        cf_candidati = [c for c in cfs if c != cfg.get("cf_studio")]
        piva_nuova = candidate[0] if len(candidate) == 1 else None
        cf_nuovo = cf_candidati[0] if len(cf_candidati) == 1 else None
        if piva_nuova is None and (candidate or cf_nuovo is None):
            esito["errore"] = (f"Cliente non riconosciuto (P.IVA trovate: {pive or 'nessuna'}; "
                               f"CF trovati: {cfs or 'nessuno'})")
            return esito
        ragione = estrai_ragione_sociale(testo) or (
            f"NUOVO CLIENTE P.IVA {piva_nuova}" if piva_nuova else f"NUOVO CLIENTE CF {cf_nuovo}")
        esito["nuovo_cliente"] = {"piva": piva_nuova or "", "cf": cf_nuovo or piva_nuova or "",
                                  "ragione_sociale": ragione}

    for pat in PATTERN_NUMERO:
        m = pat.search(testo)
        if m:
            esito["numero"] = m.group(1).strip().rstrip(".")
            break
    for pat in PATTERN_DATA_DOC:
        m = pat.search(testo)
        if m:
            esito["data"] = _parse_data(m.group(1))
            break
    if esito["data"] is None:
        esito["data"] = _parse_data(testo)
    for pat in PATTERN_TOTALE:
        m = pat.search(testo)
        if m:
            esito["totale"] = parse_importo_it(m.group(1))
            break
    for pat in PATTERN_SCADENZA:
        m = pat.search(testo)
        if m:
            esito["scadenza"] = _parse_data(m.group(1))
            break

    mancanti = [k for k in ("numero", "data", "totale") if not esito[k]]
    if mancanti:
        esito["errore"] = f"Dati non trovati nel PDF: {', '.join(mancanti)}"
        return esito
    esito["ok"] = True
    return esito


def lista_inbox():
    INBOX.mkdir(exist_ok=True)
    return sorted(p for p in INBOX.iterdir() if p.suffix.lower() == ".pdf")


def segna_duplicati(esiti, fatture):
    """Marca come errore i PDF che corrispondono a una fattura già registrata
    (stesso cliente, stesso numero, stessa data) o doppi dentro la stessa INBOX."""
    viste = {(f["codice"], f["numero"], f["data"]) for f in fatture}
    for e in esiti:
        if not e["ok"] or e["cliente"] is None:
            continue
        chiave = (e["cliente"]["codice"], str(e["numero"]), f"{e['data']:%d/%m/%Y}")
        if chiave in viste:
            e["ok"] = False
            e["errore"] = (f"Già registrata: FT {e['numero']} del {e['data']:%d/%m/%Y} "
                           "esiste già per questo cliente")
        else:
            viste.add(chiave)
    return esiti


def analizza_inbox():
    """Analizza tutti i PDF della INBOX senza registrare nulla (anteprima)."""
    return analizza_tutto()["esiti"]


def pagamenti_collegati(f, acconti):
    """I pagamenti (righe del foglio Acconti) che contengono una quota di questa fattura:
    stesso cliente, stesso numero e dicitura del pagamento presente nella nota della fattura."""
    collegati = []
    for acc in acconti:
        if acc["codice"] != f["codice"]:
            continue
        data_str = f"{acc['data']:%d/%m/%Y}" if acc["data"] else ""
        for numero, q_saldo, q_acconto in RE_QUOTE_ACCONTO.findall(acc["nota"]):
            if numero.strip() != f["numero"]:
                continue
            _, dicitura = _dicitura_quota(q_saldo, q_acconto, data_str)
            if dicitura in f["nota"]:
                collegati.append(acc)
                break
    return collegati


def analizza_cartelle(wb, fatture=None, acconti=None):
    """Confronta le fatture registrate con i PDF nelle cartelle CLIENTI.
    Ritorna (mancanti, orfani, n_senza_pdf, avviso, cartelle_mancanti):
    - mancanti: fatture APERTE il cui PDF non c'è più nella cartella del cliente
      (né in SALDATE): sono state tolte a mano e vanno eliminate dall'app;
    - orfani: PDF presenti nelle cartelle clienti ma non registrati (solo segnalati);
    - n_senza_pdf: fatture senza PDF (a mano / storiche), non controllabili;
    - cartelle_mancanti: clienti con fatture aperte la cui INTERA cartella non c'è più
      (rinominata o spostata per sbaglio): solo segnalati, mai eliminati in blocco.
    Le fatture saldate (PDF in SALDATE) non vengono controllate."""
    clienti = {c["codice"]: c for c in leggi_anagrafica(wb)}
    fatture = fatture if fatture is not None else leggi_fatture(wb)
    acconti = acconti if acconti is not None else leggi_acconti(wb)
    try:
        cartelle_ok = CARTELLA_CLIENTI.is_dir()
    except OSError:
        cartelle_ok = False
    if not cartelle_ok:
        return [], [], 0, "Cartella CLIENTI non raggiungibile: controllo dei PDF rimossi saltato.", []
    mancanti, registrati, n_senza_pdf, cartelle_mancanti = [], set(), 0, {}
    for f in fatture:
        cli = clienti.get(f["codice"])
        if not f["file"] or cli is None:
            n_senza_pdf += 1
            continue
        registrati.add((nome_cartella_cliente(cli).lower(), f["file"].lower()))
        if f["stato"] != "Aperta":
            continue
        cartella = cartella_di(cli)
        if (cartella / f["file"]).exists():
            continue
        if (SALDATE / nome_pdf_saldata(f["file"], cli)).exists():
            continue  # spostato in SALDATE: non è stato tolto
        if not cartella.is_dir():
            # cartella intera sparita: quasi certamente rinominata/spostata per errore,
            # non si eliminano tutte le fatture del cliente
            voce = cartelle_mancanti.setdefault(cli["codice"], {
                "cliente": cli, "cartella": cartella.name, "fatture": []})
            voce["fatture"].append(f)
            continue
        mancanti.append({
            "fattura": f, "cliente": cli,
            "pagamenti": pagamenti_collegati(f, acconti),
        })
    orfani = []
    for cartella in sorted(CARTELLA_CLIENTI.iterdir()):
        if not cartella.is_dir():
            continue
        for pdf in sorted(cartella.iterdir()):
            if pdf.suffix.lower() != ".pdf":
                continue
            if (cartella.name.lower(), pdf.name.lower()) not in registrati:
                orfani.append({"cartella": cartella.name, "file": pdf.name})
    return mancanti, orfani, n_senza_pdf, None, list(cartelle_mancanti.values())


def analizza_tutto():
    """Analisi completa senza registrare nulla (anteprima): PDF nuovi nella INBOX,
    fatture il cui PDF è stato tolto dalla cartella del cliente, PDF non registrati,
    cartelle cliente sparite."""
    cfg = carica_config()
    wb = apri_excel()
    clienti = leggi_anagrafica(wb)
    fatture = leggi_fatture(wb)
    mancanti, orfani, n_senza_pdf, avviso, cartelle_mancanti = analizza_cartelle(wb, fatture)
    # una fattura tolta dalla cartella e rimessa nella INBOX non è un doppione:
    # alla conferma la vecchia viene eliminata e la nuova registrata
    righe_mancanti = {m["fattura"]["riga"] for m in mancanti}
    esiti = segna_duplicati([analizza_pdf(p, clienti, cfg) for p in lista_inbox()],
                            [f for f in fatture if f["riga"] not in righe_mancanti])
    return {"esiti": esiti, "mancanti": mancanti, "orfani": orfani,
            "n_senza_pdf": n_senza_pdf, "avviso": avviso,
            "cartelle_mancanti": cartelle_mancanti}


def _registra_esiti(wb, clienti, validi):
    """Scrive nell'Excel le fatture valide lette dalla INBOX. Ritorna (messaggi, spostamenti)
    con spostamenti = [(PDF nella INBOX, destinazione nella cartella cliente)]."""
    messaggi, spostamenti = [], []
    for e in validi:
        cliente = e["cliente"]
        if cliente is None:  # cliente nuovo
            nc = e["nuovo_cliente"]
            # se nella stessa INBOX c'erano più fatture dello stesso cliente nuovo, riuso quello creato
            cliente = cliente_esistente(clienti, nc["piva"], nc["cf"])
            if cliente is None:
                cliente = crea_cliente(wb, clienti, nc["ragione_sociale"], None, nc["piva"], nc["cf"])
                if cliente is None:
                    messaggi.append(f"{e['file']}: anagrafica piena, saltata.")
                    continue
                messaggi.append(f"Nuovo cliente creato: {cliente['codice']} - {cliente['ragione_sociale']} "
                                "(controllare i dati nella pagina Clienti)")

        num_file = sanifica_nome(str(e["numero"]).replace("/", "-"))
        nome_pdf = f"FT {num_file} del {e['data']:%d-%m-%Y}.pdf"
        dest = cartella_di(cliente) / nome_pdf
        i = 2
        while dest.exists() or any(d == dest for _, d in spostamenti):
            dest = cartella_di(cliente) / f"{nome_pdf[:-4]} ({i}).pdf"
            i += 1
        scrivi_fattura(wb, cliente, e["numero"], e["data"], e["scadenza"],
                       e["totale"], dest.name)
        aggiorna_dovuto(wb, cliente["codice"], e["totale"])
        spostamenti.append((INBOX / e["file"], dest))
        messaggi.append(f"{e['file']} → {dest.parent.name} | € {euro(e['totale'])}"
                        + ("" if e["scadenza"] else " (SCADENZA NON TROVATA)"))
    return messaggi, spostamenti


def sincronizza():
    """Applica l'analisi: elimina le fatture il cui PDF è stato tolto dalla cartella del
    cliente (annullando i pagamenti collegati) e registra i PDF validi della INBOX.
    Ritorna (ok, lista di messaggi)."""
    if not excel_scrivibile():
        return False, ["Il file Excel è aperto in un altro programma: chiudilo e riprova."]
    an = analizza_tutto()
    validi = [e for e in an["esiti"] if e["ok"]]
    mancanti = an["mancanti"]
    if not validi and not mancanti:
        return False, ["Niente da fare: nessuna fattura valida nella INBOX e nessun PDF rimosso."] + \
               [f"{e['file']}: {e['errore']}" for e in an["esiti"] if not e["ok"]]

    fai_backup()
    wb = apri_excel()
    clienti = leggi_anagrafica(wb)
    messaggi, da_ritimbrare = [], []
    # 1) fatture tolte dalle cartelle: prima i pagamenti collegati, poi la riga
    for m in mancanti:
        f, cli = m["fattura"], m["cliente"]
        for acc in m["pagamenti"]:
            toccate, avvisi = _annulla_pagamento_excel(wb, acc)
            data_str = f"{acc['data']:%d/%m/%Y}" if acc["data"] else "?"
            altre = [x for x, _ in toccate if x["riga"] != f["riga"]]
            messaggi.append(f"Pagamento di € {euro(acc['importo'])} del {data_str} annullato"
                            + (" (copriva anche " + ", ".join(f"FT {x['numero']}" for x in altre)
                               + ": ora tornano aperte)" if altre else ""))
            messaggi += avvisi
            da_ritimbrare.append((cli, [(x, n) for x, n in toccate if x["riga"] != f["riga"]]))
        f_att = next((x for x in leggi_fatture(wb) if x["riga"] == f["riga"]), f)
        _elimina_riga_fattura(wb, f_att)
        messaggi.append(f"ELIMINATA FT {f['numero']} del {f['data']} di {cli['ragione_sociale']} "
                        f"(€ {euro(f['totale'])}): PDF tolto dalla cartella del cliente")
    # 2) fatture nuove dalla INBOX
    msg_reg, spostamenti = _registra_esiti(wb, clienti, validi)
    messaggi += msg_reg
    try:
        salva_excel(wb)
    except PermissionError:
        return False, ["Excel bloccato durante il salvataggio: chiudi il file e riprova. Nulla è stato registrato."]
    # 3) file: copie originali delle fatture eliminate, timbri delle altre fatture, spostamenti
    for m in mancanti:
        orig = percorso_originale(m["fattura"]["file"], m["cliente"])
        try:
            if orig.exists():
                orig.unlink()
        except OSError:
            pass
    for cli, toccate in da_ritimbrare:
        if toccate:
            _, avvisi = _annulla_pagamento_pdf(cli, toccate)
            messaggi += avvisi
    for orig, dest in spostamenti:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            orig.rename(dest)
        except OSError as e:
            # es. PDF aperto in un lettore su un altro PC: la fattura è registrata,
            # il file va spostato a mano (la prossima Analisi lo segnala come mancante)
            messaggi.append(f"ATTENZIONE — {orig.name}: registrata ma PDF NON spostato "
                            f"({e.__class__.__name__}). Chiudere il file e spostarlo a mano in "
                            f"CLIENTI\\{dest.parent.name}\\{dest.name}, oppure ripremere Analizza.")
    for e in an["esiti"]:
        if not e["ok"]:
            messaggi.append(f"NON ELABORATA — {e['file']}: {e['errore']}")
    return True, messaggi


registra_inbox = sincronizza  # nome storico


def registra_fattura_manuale(codice, nuovo, numero, data_str, scadenza_str, totale_str, pdf_bytes=None):
    """Registra una fattura scritta a mano. codice=None -> crea il cliente con i dati in `nuovo`
    (ragione_sociale, nome, piva, cf). pdf_bytes = contenuto del PDF caricato (facoltativo).
    Ritorna (ok, messaggio)."""
    if not excel_scrivibile():
        return False, "Il file Excel è aperto in un altro programma: chiudilo e riprova."
    numero = str(numero or "").strip().removeprefix("FT ").strip()
    if not numero:
        return False, "Numero della fattura mancante."
    try:
        data = datetime.strptime(data_str, "%d/%m/%Y")
        scadenza = datetime.strptime(scadenza_str, "%d/%m/%Y") if scadenza_str else None
        totale = parse_importo_it(totale_str)
    except ValueError:
        return False, "Data o importo non validi (usare gg/mm/aaaa e importi tipo 1.234,56)."
    if totale <= 0:
        return False, "L'importo deve essere maggiore di zero."
    if pdf_bytes is not None and not pdf_bytes.startswith(b"%PDF"):
        return False, "Il file caricato non è un PDF."

    wb = apri_excel()
    clienti = leggi_anagrafica(wb)
    if codice is not None:
        cliente = next((c for c in clienti if c["codice"] == int(codice)), None)
        if cliente is None:
            return False, f"Cliente {codice} non trovato."
    else:
        nuovo = nuovo or {}
        if not str(nuovo.get("ragione_sociale") or "").strip():
            return False, "Per creare il cliente serve almeno la ragione sociale (o il cognome)."
        doppio = cliente_esistente(clienti, nuovo.get("piva"), nuovo.get("cf"))
        if doppio:
            return False, (f"Esiste già il cliente {doppio['codice']} - {doppio['ragione_sociale']} "
                           "con questa P.IVA / codice fiscale: sceglierlo dall'elenco.")
        if not (normalizza_piva(nuovo.get("piva")) or str(nuovo.get("cf") or "").strip()):
            simile = cliente_con_nome_simile(clienti, nuovo["ragione_sociale"], nuovo.get("nome"))
            if simile:
                return False, (f"Nome troppo simile al cliente esistente {simile['codice']} - {simile['ragione_sociale']}"
                               f"{' ' + simile['nome'] if simile['nome'] else ''}: sceglierlo dall'elenco, oppure "
                               "indicare P.IVA o codice fiscale se è un cliente diverso.")
        cliente = None

    fatture = leggi_fatture(wb)
    if cliente and any(f["codice"] == cliente["codice"] and f["numero"] == numero
                       and f["data"] == f"{data:%d/%m/%Y}" for f in fatture):
        return False, f"Già registrata: FT {numero} del {data:%d/%m/%Y} esiste già per questo cliente."

    fai_backup()
    creato = False
    if cliente is None:
        cliente = crea_cliente(wb, clienti, nuovo["ragione_sociale"], nuovo.get("nome"),
                               nuovo.get("piva"), nuovo.get("cf"))
        if cliente is None:
            return False, "Anagrafica piena: contattare l'assistenza per ampliare il foglio."
        creato = True

    dest = None
    if pdf_bytes is not None:
        num_file = sanifica_nome(numero.replace("/", "-"))
        nome_pdf = f"FT {num_file} del {data:%d-%m-%Y}.pdf"
        dest = cartella_di(cliente) / nome_pdf
        i = 2
        while dest.exists():
            dest = cartella_di(cliente) / f"{nome_pdf[:-4]} ({i}).pdf"
            i += 1
    scrivi_fattura(wb, cliente, numero, data, scadenza, totale, dest.name if dest else None)
    aggiorna_dovuto(wb, cliente["codice"], totale)
    try:
        salva_excel(wb)
    except PermissionError:
        return False, "Excel bloccato durante il salvataggio: chiudi il file e riprova. Nulla è stato registrato."
    cartella_di(cliente).mkdir(parents=True, exist_ok=True)
    if dest is not None:
        dest.write_bytes(pdf_bytes)
    msg = (f"Fattura FT {numero} del {data:%d/%m/%Y} registrata per "
           f"{cliente['codice']} - {cliente['ragione_sociale']}: € {euro(totale)}")
    if creato:
        msg += f". Nuovo cliente creato con codice {cliente['codice']} (cartella creata; dati modificabili nella pagina Clienti)"
    if dest is None:
        msg += ". Nessun PDF allegato: ai pagamenti non ci sarà nulla da timbrare"
    if not scadenza:
        msg += ". Scadenza non indicata"
    return True, msg + "."


# ============================ PAGAMENTI ============================

def leggi_acconti(wb):
    ws = wb["Acconti"]
    acconti = []
    for r in range(RIGA_DATI, ULTIMA_RIGA_REGISTRI + 1):
        codice = _come_codice(ws.cell(row=r, column=2).value)
        if codice is None:
            continue
        importo = ws.cell(row=r, column=4).value
        acconti.append({
            "riga": r, "data": _come_data(ws.cell(row=r, column=1).value),
            "codice": codice,
            "importo": float(importo) if isinstance(importo, (int, float)) else 0.0,
            "modalita": ws.cell(row=r, column=5).value or "",
            "nota": str(ws.cell(row=r, column=7).value or ""),
        })
    return acconti


def percorso_originale(nome_file, cliente):
    return ORIGINALI / nome_cartella_cliente(cliente) / nome_file


def salva_originale(pdf, cliente):
    """Conserva una copia pulita del PDF (prima del primo timbro) in ORIGINALI."""
    orig = percorso_originale(pdf.name, cliente)
    if not orig.exists():
        orig.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, orig)
    return orig


RE_DICITURE = re.compile(r"; (?:acconto € ([\d.,]+)|saldata \(€ ([\d.,]+)\)) il (\d{2}/\d{2}/\d{4})")


def rigenera_timbri(pdf, cliente, nota):
    """Riparte dall'originale pulito e riapplica solo i timbri dei pagamenti ancora
    presenti nella nota della fattura. Ritorna False se l'originale non esiste
    (PDF timbrato prima di questo aggiornamento: il timbro resta)."""
    orig = percorso_originale(pdf.name, cliente)
    if not orig.exists():
        return False
    shutil.copy2(orig, pdf)
    for i, m in enumerate(RE_DICITURE.finditer(nota)):
        q_acconto, q_saldo, data = m.groups()
        testo = f"PAGATO il {data}" if q_saldo else f"ACCONTO € {q_acconto} il {data}"
        timbra_pdf(pdf, testo, i)
    return True


def timbra_pdf(percorso, testo, posizione, cliente=None):
    if cliente is not None:
        salva_originale(Path(percorso), cliente)
    reader = PdfReader(percorso)
    pagina = reader.pages[0]
    largh, alt = float(pagina.mediabox.width), float(pagina.mediabox.height)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(largh, alt))
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.red)
    c.setStrokeColor(colors.red)
    x, y = largh - 20, alt - 30 - posizione * 22
    ampiezza = c.stringWidth(testo, "Helvetica-Bold", 11)
    c.drawRightString(x, y, testo)
    c.rect(x - ampiezza - 6, y - 6, ampiezza + 12, 20)
    c.save()
    buf.seek(0)
    writer = PdfWriter()
    pagina.merge_page(PdfReader(buf).pages[0])
    writer.add_page(pagina)
    for p in reader.pages[1:]:
        writer.add_page(p)
    with open(percorso, "wb") as f:
        writer.write(f)


def nome_pdf_saldata(nome_file, cliente):
    """Nome del PDF nella cartella unica SALDATE: 'CLIENTE - nome file originale'."""
    rs = str(cliente["ragione_sociale"]).strip()
    if cliente.get("nome"):
        rs = f"{rs} {str(cliente['nome']).strip()}"
    return f"{sanifica_nome(rs)} - {nome_file}"


def archivia_pdf_saldata(pdf, cliente):
    """Sposta il PDF di una fattura saldata nella cartella unica SALDATE,
    rinominato con il nome del cliente davanti (verrà stampato da lì)."""
    SALDATE.mkdir(parents=True, exist_ok=True)
    base = nome_pdf_saldata(pdf.name, cliente)
    dest = SALDATE / base
    i = 2
    while dest.exists():
        dest = SALDATE / f"{base[:-4]} ({i}).pdf"
        i += 1
    shutil.move(str(pdf), str(dest))
    return dest


def ripristina_pdf_saldata(nome_file, cliente):
    """Riporta un PDF dalla cartella SALDATE a quella del cliente,
    con il nome originale (annullo pagamento)."""
    orig = SALDATE / nome_pdf_saldata(nome_file, cliente)
    if not orig.exists():
        return None
    dest = cartella_di(cliente) / nome_file
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return None
    shutil.move(str(orig), str(dest))
    return dest


def registra_pagamento(codice, importo_str, data_str=None, num_fattura=None, modalita=None):
    """Registra un pagamento. Ritorna (ok, lista messaggi)."""
    if not excel_scrivibile():
        return False, ["Il file Excel è aperto in un altro programma: chiudilo e riprova."]
    try:
        importo = parse_importo_it(importo_str)
        data = datetime.strptime(data_str, "%d/%m/%Y") if data_str else datetime.today()
    except ValueError:
        return False, ["Importo o data non validi."]
    if importo <= 0:
        return False, ["L'importo deve essere maggiore di zero."]

    wb = apri_excel()
    clienti = leggi_anagrafica(wb)
    cliente = next((c for c in clienti if c["codice"] == int(codice)), None)
    if cliente is None:
        return False, [f"Cliente {codice} non trovato."]

    aperte = [f for f in leggi_fatture(wb)
              if f["codice"] == int(codice) and f["residuo"] > 0]
    aperte.sort(key=lambda f: (f["scadenza"] or datetime.max, f["riga"]))
    if num_fattura:
        aperte = [f for f in aperte if f["numero"] == num_fattura]
        if not aperte:
            return False, [f"Nessuna fattura aperta n. {num_fattura} per questo cliente."]
    if not aperte:
        return False, [f"{cliente['ragione_sociale']} non ha fatture aperte: il pagamento NON è stato "
                       "registrato. Se manca una fattura, smistarla prima dalla INBOX."]
    tot_aperto = round(sum(f["residuo"] for f in aperte), 2)
    if importo > tot_aperto + 0.005:
        return False, [f"L'importo (€ {euro(importo)}) supera quanto ancora dovuto da "
                       f"{cliente['ragione_sociale']} (€ {euro(tot_aperto)}): il pagamento NON è stato "
                       "registrato. Se manca una fattura, smistarla prima dalla INBOX; "
                       "altrimenti correggere l'importo."]

    fai_backup()
    ws = wb["Insoluti"]
    rimanente, toccate, messaggi = importo, [], []
    for f in aperte:
        if rimanente <= 0:
            break
        quota = min(f["residuo"], rimanente)
        nuovo_residuo = round(f["residuo"] - quota, 2)
        rimanente = round(rimanente - quota, 2)
        ws.cell(row=f["riga"], column=5).value = nuovo_residuo
        saldata = nuovo_residuo == 0
        nota = ws.cell(row=f["riga"], column=8).value or ""
        timbri = len(re.findall(r"(?:acconto € |saldata)", nota, re.I))
        aggiunta = (f"; saldata (€ {euro(quota)}) il {data:%d/%m/%Y}" if saldata
                    else f"; acconto € {euro(quota)} il {data:%d/%m/%Y}")
        ws.cell(row=f["riga"], column=8).value = nota + aggiunta
        toccate.append((f, quota, saldata, timbri))

    wa = wb["Acconti"]
    ra = prima_riga_libera(wa, colonna=2)
    cella_data = wa.cell(row=ra, column=1)
    cella_data.value = data
    cella_data.number_format = "DD/MM/YYYY"
    wa.cell(row=ra, column=2).value = int(codice)
    wa.cell(row=ra, column=3).value = (
        f'=IF($B{ra}="","",IFERROR(INDEX(Clienti!$B:$B,MATCH($B{ra},Clienti!$A:$A,0)),"Codice non trovato"))')
    cella_imp = wa.cell(row=ra, column=4)
    cella_imp.value = importo
    cella_imp.number_format = '#,##0.00" €"'
    if modalita:
        wa.cell(row=ra, column=5).value = modalita
    wa.cell(row=ra, column=6).value = trimestre(data)
    wa.cell(row=ra, column=7).value = ", ".join(
        f"FT {f['numero']}" + (f" saldata (€ {euro(q)})" if s else f" acconto € {euro(q)}")
        for f, q, s, _ in toccate) or "nessuna fattura aperta"
    try:
        salva_excel(wb)
    except PermissionError:
        return False, ["Excel bloccato durante il salvataggio: chiudi il file e riprova."]

    cartella = cartella_di(cliente)
    for f, quota, saldata, timbri in toccate:
        pdf = cartella / f["file"] if f["file"] else None
        if pdf is None or not pdf.exists():
            messaggi.append(f"FT {f['numero']}: PDF non trovato, timbro saltato.")
            continue
        testo = (f"PAGATO il {data:%d/%m/%Y}" if saldata
                 else f"ACCONTO € {euro(quota)} il {data:%d/%m/%Y}")
        try:
            timbra_pdf(pdf, testo, timbri, cliente)
        except Exception as e:
            messaggi.append(f"FT {f['numero']}: errore nel timbro ({e}).")
        if saldata:
            try:
                archivia_pdf_saldata(pdf, cliente)
            except Exception as e:
                messaggi.append(f"FT {f['numero']}: PDF non spostato in SALDATE ({e}).")

    messaggi.insert(0, f"Registrati € {euro(importo)} da {cliente['ragione_sociale']} il {data:%d/%m/%Y}.")
    for f, quota, saldata, _ in toccate:
        messaggi.append(f"FT {f['numero']}: " +
                        ("SALDATA — PDF archiviato in SALDATE" if saldata
                         else f"acconto € {euro(quota)}, resta aperta"))
    return True, messaggi


def elimina_pagamento(riga):
    """Annulla un pagamento: toglie la riga Acconti, ripristina i residui delle fatture
    e riporta i PDF allo stato precedente (via i timbri di quel pagamento)."""
    if not excel_scrivibile():
        return False, "Il file Excel è aperto in un altro programma: chiudilo e riprova."
    wb = apri_excel()
    acc = next((a for a in leggi_acconti(wb) if a["riga"] == int(riga)), None)
    if acc is None:
        return False, "Pagamento non trovato."
    fai_backup()
    cliente = next((c for c in leggi_anagrafica(wb) if c["codice"] == acc["codice"]), None)
    toccate, avvisi = _annulla_pagamento_excel(wb, acc)
    salva_excel(wb)
    timbri_rimasti, avvisi_pdf = _annulla_pagamento_pdf(cliente, toccate)
    avvisi += avvisi_pdf
    msg = "Pagamento annullato: residui ripristinati e timbri tolti dai PDF."
    if timbri_rimasti:
        msg = ("Pagamento annullato e residui ripristinati. Timbro NON rimosso su "
               + ", ".join(timbri_rimasti)
               + " (PDF timbrato prima di questo aggiornamento: manca la copia originale).")
    if avvisi:
        msg += " " + " ".join(avvisi)
    return True, msg


RE_QUOTE_ACCONTO = re.compile(r"FT (.+?) (?:saldata \(€ ([\d.,]+)\)|acconto € ([\d.,]+))")


def _dicitura_quota(q_saldo, q_acconto, data_str):
    quota = parse_importo_it(q_saldo or q_acconto)
    return quota, (f"; saldata (€ {euro(quota)}) il {data_str}" if q_saldo
                   else f"; acconto € {euro(quota)} il {data_str}")


def _annulla_pagamento_excel(wb, acc):
    """Parte Excel dell'annullo di un pagamento: toglie la riga Acconti e ripristina i
    residui delle fatture usando le quote scritte nella nota dell'acconto.
    Ritorna (toccate, avvisi) con toccate = [(fattura, nota aggiornata)]."""
    quote = RE_QUOTE_ACCONTO.findall(acc["nota"])
    ws = wb["Insoluti"]
    fatture = leggi_fatture(wb)
    data_str = f"{acc['data']:%d/%m/%Y}" if acc["data"] else ""
    avvisi, toccate, usate = [], [], set()
    for numero, q_saldo, q_acconto in quote:
        quota, dicitura = _dicitura_quota(q_saldo, q_acconto, data_str)
        # più fatture possono avere lo stesso numero: scelgo quella con la dicitura
        # di questo pagamento nella nota, e non riuso mai la stessa riga
        candidate = [x for x in fatture
                     if x["codice"] == acc["codice"] and x["numero"] == numero.strip()
                     and x["riga"] not in usate]
        f = next((x for x in candidate if dicitura in x["nota"]), None) or \
            (candidate[0] if candidate else None)
        if f is None:
            avvisi.append(f"FT {numero}: riga non trovata, residuo non ripristinato.")
            continue
        usate.add(f["riga"])
        ws.cell(row=f["riga"], column=5).value = round(f["residuo"] + quota, 2)
        nota = ws.cell(row=f["riga"], column=8).value or ""
        if dicitura in nota:
            nota = nota.replace(dicitura, "", 1)
        ws.cell(row=f["riga"], column=8).value = nota
        toccate.append((f, nota))
    wa = wb["Acconti"]
    for col in (1, 2, 4, 5, 6, 7):
        wa.cell(row=acc["riga"], column=col).value = None
    wa.cell(row=acc["riga"], column=3).value = (
        f'=IF($B{acc["riga"]}="","",IFERROR(INDEX(Clienti!$B:$B,MATCH($B{acc["riga"]},Clienti!$A:$A,0)),"Codice non trovato"))')
    return toccate, avvisi


def _annulla_pagamento_pdf(cliente, toccate):
    """Parte PDF dell'annullo: la fattura torna aperta -> se sta in SALDATE torna dal
    cliente, poi via i timbri di quel pagamento. Ritorna (timbri_rimasti, avvisi)."""
    timbri_rimasti, avvisi = [], []
    for f, nota in toccate:
        if not cliente or not f["file"]:
            continue
        pdf = cartella_di(cliente) / f["file"]
        if not pdf.exists():
            if ripristina_pdf_saldata(f["file"], cliente):
                avvisi.append(f"FT {f['numero']}: PDF riportato nella cartella del cliente.")
        if not pdf.exists():
            avvisi.append(f"FT {f['numero']}: PDF non trovato, timbri non aggiornati.")
            continue
        try:
            if not rigenera_timbri(pdf, cliente, nota):
                timbri_rimasti.append(f"FT {f['numero']}")
        except Exception as e:
            avvisi.append(f"FT {f['numero']}: errore nell'aggiornare i timbri ({e}).")
    return timbri_rimasti, avvisi


# ============================ RIEPILOGO E REPORT ============================

MESI_IT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def andamento_mensile(fatture, n_mesi=12, oggi=None):
    """Per ciascuno degli ultimi n_mesi (mese di emissione della fattura): fatturato,
    incassato (totale - residuo), da incassare (residuo) e numero di fatture."""
    oggi = oggi or datetime.now()
    mesi, a, m = [], oggi.year, oggi.month
    for _ in range(n_mesi):
        mesi.append((a, m))
        m -= 1
        if m == 0:
            a, m = a - 1, 12
    mesi.reverse()
    agg = {k: {"fatturato": 0.0, "incassato": 0.0, "da_incassare": 0.0, "n": 0} for k in mesi}
    for f in fatture:
        d = _parse_data(f["data"]) if f["data"] else None
        if d is None or (d.year, d.month) not in agg:
            continue
        v = agg[(d.year, d.month)]
        v["fatturato"] += f["totale"]
        v["da_incassare"] += f["residuo"]
        v["incassato"] += f["totale"] - f["residuo"]
        v["n"] += 1
    return [{"anno": a, "mese": m, "etichetta": f"{MESI_IT[m - 1]} {str(a)[2:]}",
             **{k: round(x, 2) for k, x in agg[(a, m)].items()}} for a, m in mesi]


def _passo_griglia(massimo):
    """Passo 'pulito' per le tacche dell'asse (al massimo 5 intervalli)."""
    for passo in (100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000, 25000, 50000, 100000):
        if massimo / passo <= 5:
            return passo
    return 200000


def _rettangolo_arrotondato(x, y, w, h, r=4):
    """Path SVG di un rettangolo con i soli angoli superiori arrotondati."""
    r = min(r, w / 2, h)
    return (f"M{x:.1f},{y + h:.1f} V{y + r:.1f} a{r},{r} 0 0 1 {r},-{r} "
            f"h{w - 2 * r:.1f} a{r},{r} 0 0 1 {r},{r} V{y + h:.1f} Z")


def grafico_mensile(andamento, larg=760, alt=230):
    """Geometria del grafico SVG a barre impilate (incassato sotto, da incassare sopra;
    l'altezza totale è il fatturato del mese)."""
    sin, des, sopra, sotto = 58, 14, 28, 30
    area_h = alt - sopra - sotto
    y_base = sopra + area_h
    massimo = max((v["fatturato"] for v in andamento), default=0) or 1
    passo = _passo_griglia(massimo)
    tacche = [i * passo for i in range(0, int(massimo // passo) + 2)]
    massimo = tacche[-1]
    n = max(len(andamento), 1)
    spazio = (larg - sin - des) / n
    bw = min(34, spazio * 0.62)
    barre = []
    for i, v in enumerate(andamento):
        x = sin + i * spazio + (spazio - bw) / 2
        h_inc = area_h * v["incassato"] / massimo
        h_da = area_h * v["da_incassare"] / massimo
        gap = 2 if (h_inc >= 1 and h_da >= 1) else 0
        y_inc = y_base - h_inc
        y_da = y_inc - gap - h_da
        barre.append({
            **v, "x": round(x, 1), "bw": round(bw, 1), "x_centro": round(x + bw / 2, 1),
            "y_inc": round(y_inc, 1), "h_inc": round(h_inc, 1),
            "y_da": round(y_da, 1), "h_da": round(h_da, 1),
            "y_top": round(y_da if h_da >= 1 else y_inc, 1),
            "path_inc": _rettangolo_arrotondato(x, y_inc, bw, h_inc) if h_inc >= 1 and h_da < 1 else None,
            "path_da": _rettangolo_arrotondato(x, y_da, bw, h_da) if h_da >= 1 else None,
        })
    massimo_mese = max(barre, key=lambda b: b["fatturato"], default=None)
    for b in barre:
        # etichette dirette solo sul mese più alto e sull'ultimo (gli altri via tooltip)
        b["etichetta_valore"] = b is massimo_mese or b is barre[-1]
    griglia = [{"y": round(y_base - area_h * t / massimo, 1), "val": t,
                "testo": euro(t)[:-3] if t else "0"} for t in tacche]   # tacche senza decimali
    return {"larg": larg, "alt": alt, "barre": barre, "griglia": griglia,
            "y_base": y_base, "x_inizio": sin, "x_fine": larg - des,
            "tot_fatturato": round(sum(v["fatturato"] for v in andamento), 2),
            "tot_incassato": round(sum(v["incassato"] for v in andamento), 2),
            "tot_da_incassare": round(sum(v["da_incassare"] for v in andamento), 2)}


def riepilogo():
    wb = apri_excel()
    clienti = leggi_anagrafica(wb)
    fatture = leggi_fatture(wb)
    aperte = [f for f in fatture if f["residuo"] > 0]
    per_nome = lambda f: (chiave_nome(f["cliente"]), f["scadenza"] or datetime.max, f["riga"])
    scadute = sorted([f for f in aperte if f["ritardo"]], key=per_nome)
    situazione = situazione_clienti(wb, fatture)
    nomi = {c["codice"]: c["ragione_sociale"] for c in clienti}
    per_cliente = sorted(
        [dict(codice=k, cliente=nomi.get(k, "?"), **v) for k, v in situazione.items()
         if v["fatturato"] or v["incassato"]],
        key=lambda v: chiave_nome(v["cliente"]))
    return {
        "n_clienti": len(clienti),
        "tot_aperto": sum(f["residuo"] for f in aperte),
        "n_aperte": len(aperte),
        "scadute": scadute,
        "aperte": sorted(aperte, key=per_nome),
        "fatture": fatture,
        "situazione": situazione,
        "per_cliente": per_cliente,
        "andamento": andamento_mensile(fatture),
    }


BLU_PDF = colors.HexColor("#4a687d")


def _documento_pdf(percorso, titolo, testo_destra):
    """Documento A4 con l'intestazione dello studio (logo + dati a sinistra, titolo e
    testo a destra). Ritorna (doc, corpo, stili, blu, stile_base) pronti per le tabelle."""
    doc = SimpleDocTemplate(str(percorso), pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    stili = getSampleStyleSheet()
    blu = BLU_PDF
    studio = dati_studio()
    stile_studio = ParagraphStyle("studio", parent=stili["Normal"], fontSize=8.5, leading=11,
                                  textColor=colors.HexColor("#44586c"))
    stile_titolo = ParagraphStyle("titolo", parent=stili["Normal"], fontSize=15, leading=18,
                                  fontName="Helvetica-Bold", textColor=blu, alignment=2)
    stile_data = ParagraphStyle("data", parent=stile_studio, alignment=2)
    # intestazione senza logo: solo le righe compilate nelle Impostazioni
    righe = [f"<b>{escape(studio['nome'])}</b>"] if studio["nome"] else []
    fiscali = " - ".join(x for x in (studio["piva"] and f"P.IVA {studio['piva']}",
                                     studio["cf"] and f"C.F. {studio['cf']}") if x)
    contatti = " - ".join(x for x in (studio["telefono"] and f"Tel. {studio['telefono']}",
                                      studio["email"]) if x)
    righe += [escape(x) for x in (fiscali, studio["indirizzo"], contatti) if x]
    blocco_sx = [Paragraph("<br/>".join(righe) or "&nbsp;", stile_studio)]
    blocco_dx = [Paragraph(titolo, stile_titolo), Spacer(1, 6), Paragraph(testo_destra, stile_data)]
    testata = Table([[blocco_sx, blocco_dx]], colWidths=[10 * cm, 8 * cm])
    testata.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                 ("LINEBELOW", (0, 0), (-1, 0), 1.2, blu), ("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
    corpo = [testata, Spacer(1, 12)]
    stile_base = [("BACKGROUND", (0, 0), (-1, 0), blu),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                  ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f7")])]
    return doc, corpo, stili, blu, stile_base


def genera_report_pdf(percorso):
    """Report PDF della situazione crediti aperti, raggruppato per cliente."""
    dati = riepilogo()
    doc, corpo, stili, blu, stile_base = _documento_pdf(
        percorso, "Scadenziario<br/>Situazione crediti aperti",
        f"Generato il {datetime.now():%d/%m/%Y alle %H:%M}<br/>"
        f"Totale aperto: <b>€ {euro(dati['tot_aperto'])}</b> su {dati['n_aperte']} fatture")
    # tabella unica: fatture aperte in ordine alfabetico di cliente (poi per data),
    # con il subtotale dei clienti che hanno più fatture e il totale generale in fondo
    corpo.append(Paragraph("Fatture aperte per cliente (ordine alfabetico)", stili["Heading2"]))
    aperte = sorted(dati["aperte"], key=lambda f: (chiave_nome(f["cliente"]),
                                                   _parse_data(f["data"]) or datetime.max, f["riga"]))
    righe = [["Cliente", "Fattura", "Data", "Scadenza", "Ritardo", "Totale €", "Residuo €"]]
    stile = stile_base + [("ALIGN", (-2, 1), (-1, -1), "RIGHT")]
    grigio = colors.HexColor("#e6edf2")
    i = 0
    while i < len(aperte):
        gruppo = [f for f in aperte if f["codice"] == aperte[i]["codice"]]
        for f in gruppo:
            righe.append([f"{f['codice']} - {f['cliente']}"[:40], f"FT {f['numero']}", f["data"],
                          f"{f['scadenza']:%d/%m/%Y}" if f["scadenza"] else "-",
                          f"{f['ritardo']} gg" if f["ritardo"] else "-", euro(f["totale"]), euro(f["residuo"])])
            if f["ritardo"]:
                stile.append(("TEXTCOLOR", (4, len(righe) - 1), (4, len(righe) - 1), colors.red))
        if len(gruppo) > 1:
            righe.append([f"Totale {gruppo[0]['cliente']}"[:40], f"{len(gruppo)} fatture", "", "", "",
                          euro(sum(f["totale"] for f in gruppo)), euro(sum(f["residuo"] for f in gruppo))])
            r = len(righe) - 1
            stile += [("BACKGROUND", (0, r), (-1, r), grigio), ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]
        i += len(gruppo)
    if len(righe) == 1:
        corpo.append(Paragraph("Nessuna fattura aperta. Tutto incassato.", stili["Normal"]))
    else:
        righe.append(["TOTALE GENERALE", f"{len(aperte)} fatture", "", "", "",
                      euro(sum(f["totale"] for f in aperte)), euro(sum(f["residuo"] for f in aperte))])
        r = len(righe) - 1
        stile += [("BACKGROUND", (0, r), (-1, r), blu), ("TEXTCOLOR", (0, r), (-1, r), colors.white),
                  ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]
        tab = Table(righe, colWidths=[6.8 * cm, 2.3 * cm, 1.9 * cm, 1.9 * cm, 1.3 * cm, 1.9 * cm, 1.9 * cm],
                    repeatRows=1)
        tab.setStyle(TableStyle(stile))
        corpo.append(tab)
    doc.build(corpo)
    return percorso


# ============================ SCHEDA CLIENTE ============================

def scheda_cliente(codice, wb=None):
    """Tutto quello che riguarda un cliente: anagrafica, fatture (in ordine di data),
    pagamenti (dal più recente) e totali. None se il codice non esiste."""
    wb = wb or apri_excel()
    cliente = next((c for c in leggi_anagrafica(wb) if c["codice"] == codice), None)
    if cliente is None:
        return None
    fatture = sorted([f for f in leggi_fatture(wb) if f["codice"] == codice],
                     key=lambda f: (_parse_data(f["data"]) or datetime.max, f["riga"]))
    pagamenti = sorted([a for a in leggi_acconti(wb) if a["codice"] == codice],
                       key=lambda a: (a["data"] or datetime.min, a["riga"]), reverse=True)
    aperte = [f for f in fatture if f["residuo"] > 0]
    scadute = [f for f in aperte if f["ritardo"]]
    voce = situazione_clienti(wb, fatture, pagamenti).get(
        codice, {"fatturato": 0.0, "incassato": 0.0, "da_incassare": 0.0, "n_aperte": 0, "credito": 0.0})
    return {
        "cliente": cliente,
        "nome_completo": f"{cliente['ragione_sociale']} {cliente['nome'] or ''}".strip(),
        "fatture": fatture, "aperte": aperte, "scadute": scadute, "pagamenti": pagamenti,
        "n_fatture": len(fatture), "n_aperte": len(aperte), "n_scadute": len(scadute),
        "fatturato": voce["fatturato"], "incassato": voce["incassato"],
        "da_incassare": voce["da_incassare"], "credito": voce["credito"],
        "tot_scaduto": round(sum(f["residuo"] for f in scadute), 2),
    }


def nome_pdf_scheda(cliente, quando=None):
    quando = quando or datetime.now()
    return f"{nome_cartella_cliente(cliente)} - scheda {quando:%d-%m-%Y}.pdf"


def genera_scheda_cliente_pdf(codice, percorso=None):
    """PDF della scheda di un cliente (situazione fatture e pagamenti), pronto da inviare.
    Salvato in dati/SCHEDE CLIENTI se non si indica un percorso. Ritorna (percorso, scheda)."""
    sc = scheda_cliente(codice)
    if sc is None:
        return None, None
    if percorso is None:
        SCHEDE.mkdir(parents=True, exist_ok=True)
        percorso = SCHEDE / nome_pdf_scheda(sc["cliente"])
    c = sc["cliente"]
    doc, corpo, stili, blu, stile_base = _documento_pdf(
        percorso, "Scheda cliente<br/>Situazione fatture e pagamenti",
        f"Aggiornata al {datetime.now():%d/%m/%Y alle %H:%M}<br/>"
        f"Da incassare: <b>€ {euro(sc['da_incassare'])}</b> su {sc['n_aperte']} fatture aperte")
    # la scheda è più ariosa del report generale: carattere 10 e celle più alte
    stile_base = [v for v in stile_base if v[0] != "FONTSIZE"] + [
        ("FONTSIZE", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    stili["Heading2"].fontSize = 14
    stili["Heading2"].spaceBefore = 8
    normale = ParagraphStyle("n", parent=stili["Normal"], fontSize=10.5, leading=14)
    piccolo = ParagraphStyle("p", parent=stili["Normal"], fontSize=9.5, leading=12,
                             textColor=colors.HexColor("#44586c"))
    # riquadro anagrafico
    righe_cli = [["Cliente", f"{c['codice']} - {sc['nome_completo']}"],
                 ["Partita IVA", c["piva"] or "-"], ["Codice fiscale", c["cf"] or "-"]]
    if c.get("note"):
        righe_cli.append(["Note", str(c["note"])[:90]])
    tab_cli = Table(righe_cli, colWidths=[3.2 * cm, 14.8 * cm])
    tab_cli.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 11),
                                 ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                 ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                                 ("TEXTCOLOR", (0, 0), (0, -1), blu),
                                 ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2f7")),
                                 ("BOX", (0, 0), (-1, -1), 0.6, blu),
                                 ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    corpo += [tab_cli, Spacer(1, 12)]
    # riepilogo numerico
    riep = [["Fatture", "Fatturato", "Incassato", "Da incassare", "Aperte", "Scadute"],
            [str(sc["n_fatture"]), "€ " + euro(sc["fatturato"]), "€ " + euro(sc["incassato"]),
             "€ " + euro(sc["da_incassare"]), str(sc["n_aperte"]),
             f"{sc['n_scadute']} (€ {euro(sc['tot_scaduto'])})"]]
    tab_riep = Table(riep, colWidths=[2 * cm, 3.4 * cm, 3.4 * cm, 3.4 * cm, 2 * cm, 3.8 * cm])
    st = stile_base + [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                       ("FONTSIZE", (0, 1), (-1, 1), 11.5)]
    if sc["da_incassare"] > 0:
        st.append(("TEXTCOLOR", (3, 1), (3, 1), colors.red))
    if sc["n_scadute"]:
        st.append(("TEXTCOLOR", (5, 1), (5, 1), colors.red))
    tab_riep.setStyle(TableStyle(st))
    corpo += [tab_riep, Spacer(1, 14)]
    # fatture aperte
    corpo.append(Paragraph("Fatture aperte", stili["Heading2"]))
    if not sc["aperte"]:
        corpo.append(Paragraph("Nessuna fattura aperta: tutto incassato.", normale))
    else:
        righe = [["Fattura", "Data", "Scadenza", "Ritardo", "Totale €", "Pagato €", "Residuo €"]]
        st = stile_base + [("ALIGN", (3, 1), (-1, -1), "RIGHT")]
        for f in sc["aperte"]:
            righe.append([f"FT {f['numero']}", f["data"],
                          f"{f['scadenza']:%d/%m/%Y}" if f["scadenza"] else "-",
                          f"{f['ritardo']} gg" if f["ritardo"] else "-",
                          euro(f["totale"]), euro(round(f["totale"] - f["residuo"], 2)), euro(f["residuo"])])
            if f["ritardo"]:
                st.append(("TEXTCOLOR", (3, len(righe) - 1), (3, len(righe) - 1), colors.red))
        righe.append(["TOTALE", f"{len(sc['aperte'])} fatture", "", "",
                      euro(sum(f["totale"] for f in sc["aperte"])),
                      euro(sum(f["totale"] - f["residuo"] for f in sc["aperte"])), euro(sc["da_incassare"])])
        r = len(righe) - 1
        st += [("BACKGROUND", (0, r), (-1, r), blu), ("TEXTCOLOR", (0, r), (-1, r), colors.white),
               ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]
        tab = Table(righe, colWidths=[3.6 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm, 2.7 * cm, 2.7 * cm, 2.8 * cm],
                    repeatRows=1)
        tab.setStyle(TableStyle(st))
        corpo.append(tab)
    corpo.append(Spacer(1, 12))
    # fatture saldate
    saldate = [f for f in sc["fatture"] if f["residuo"] <= 0]
    if saldate:
        corpo.append(Paragraph("Fatture saldate", stili["Heading2"]))
        righe = [["Fattura", "Data", "Scadenza", "Totale €"]]
        for f in saldate:
            righe.append([f"FT {f['numero']}", f["data"],
                          f"{f['scadenza']:%d/%m/%Y}" if f["scadenza"] else "-", euro(f["totale"])])
        tab = Table(righe, colWidths=[4 * cm, 3 * cm, 3 * cm, 3 * cm], repeatRows=1, hAlign="LEFT")
        tab.setStyle(TableStyle(stile_base + [("ALIGN", (3, 1), (-1, -1), "RIGHT")]))
        corpo += [tab, Spacer(1, 12)]
    # pagamenti
    corpo.append(Paragraph("Pagamenti ricevuti", stili["Heading2"]))
    if not sc["pagamenti"]:
        corpo.append(Paragraph("Nessun pagamento registrato.", normale))
    else:
        righe = [["Data", "Importo €", "Modalità", "Riferimento"]]
        for a in sc["pagamenti"]:
            righe.append([f"{a['data']:%d/%m/%Y}" if a["data"] else "-", euro(a["importo"]),
                          str(a["modalita"] or "-")[:18], Paragraph(str(a["nota"] or "")[:160], piccolo)])
        righe.append(["TOTALE INCASSATO", euro(sc["incassato"]), "", ""])
        r = len(righe) - 1
        tab = Table(righe, colWidths=[2.4 * cm, 2.6 * cm, 3 * cm, 10 * cm], repeatRows=1)
        tab.setStyle(TableStyle(stile_base + [("ALIGN", (1, 1), (1, -1), "RIGHT"),
                                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                              ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#e6edf2")),
                                              ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]))
        corpo.append(tab)
    corpo.append(Spacer(1, 16))
    doc.build(corpo)
    return percorso, sc
