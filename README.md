# Receivables Tracker — issued invoices and collections, from PDFs only

A local web app (Python/Flask) that keeps track of **what clients still owe**. Drop the PDFs of issued invoices into an inbox: the app reads them, recognises the client by VAT number, files each PDF in the client's folder and registers the invoice in an Excel workbook. Payments are recorded against invoices, and the PDFs are stamped **ACCONTO** (partial) or **PAGATO** (paid) automatically.

Built and used in production at an Italian tax & payroll advisory firm: **shared across 6 workstations, 300 clients tracked starting from PDFs only.**

## What it does

| Page | Function |
|---|---|
| Riepilogo | totals, overdue invoices highlighted, monthly trend chart |
| Smistamento | reads the inbox PDFs, shows a preview (client, number, date, amount), files them on confirmation |
| Pagamenti | records full or partial payments; stamps the PDF and keeps the original |
| Fatture / Clienti | invoice list and client register, alphabetical, with per-client statement page |
| Report | PDF report of open receivables with per-client subtotals, and per-client statements in PDF |

Data lives in a plain Excel workbook (`dati/`), with the last 30 copies kept as automatic backups. The data folder can sit on a network share (`percorso_dati.txt`) so several PCs use the same records. The server only answers on `127.0.0.1`: nothing leaves the PC.

## Try it

```
pip install -r requisiti.txt
python prepara_dati.py      # creates an empty dati/ folder
python app.py               # opens http://127.0.0.1:8770
python _test_app.py         # end-to-end test: 157 checks on fictitious invoices
```

The test builds fake invoice PDFs with reportlab, runs the whole flow through Flask's test client (filing, payments, stamps, reports, client statements, edge cases such as renamed folders and rejected duplicates) and wipes its own data afterwards.

## Files

| File | Content |
|---|---|
| `app.py` | Flask routes |
| `motore.py` | Excel workbook, PDF parsing (pdfplumber), stamping (pypdf + reportlab), reports |
| `pagine.py` | HTML templates |
| `risorse/` | empty Excel template, Montserrat font |
| `SCADENZIARIO.spec` | PyInstaller config: shipped to colleagues as a single `.exe`, no Python needed |
| `docs/GUIDA SCADENZIARIO.pdf` | user guide (Italian) |

All names, VAT numbers and invoices used in tests are **fictitious**. No client data is included.

## Stack

Python · Flask · openpyxl · pdfplumber · pypdf · reportlab · PyInstaller

---

## In italiano

Web app locale in Python/Flask per le fatture emesse e gli incassi: legge i PDF delle fatture, riconosce il cliente dalla P.IVA, smista ogni PDF nella cartella del cliente e registra la fattura in un Excel; registra i pagamenti e timbra i PDF con ACCONTO o PAGATO, evidenzia le scadute, produce report e schede cliente in PDF. Dati anche condivisi in rete tra più postazioni. In produzione presso uno studio di consulenza fiscale e del lavoro: **6 postazioni, 300 clienti monitorati partendo solo dai PDF**. Collaudo automatico con 157 controlli su dati interamente fittizi.

Author: Francesco Aversano
