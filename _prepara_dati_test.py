# Dati di PROVA per _test_app.py: cartella "dati" vuota + due clienti finti e uno studio finto.
import runpy
import sys
from pathlib import Path

QUI = Path(__file__).parent
runpy.run_path(str(QUI / "prepara_dati.py"))   # dati vuoti in QUI\dati
sys.path.insert(0, str(QUI))
import motore

motore.imposta_dati(QUI / "dati")
wb = motore.apri_excel()
ws = wb["Clienti"]
for riga, (codice, nome, piva) in enumerate([(10, "BETA ESEMPIO S.R.L.S", "09876543210"),
                                             (20, "ALFA ESEMPIO S.R.L", "07654321004")], start=5):
    ws.cell(row=riga, column=1).value = codice
    ws.cell(row=riga, column=2).value = nome
    ws.cell(row=riga, column=4).value = piva
    ws.cell(row=riga, column=5).value = piva
motore.salva_excel(wb)
for c in motore.leggi_anagrafica(motore.apri_excel()):
    motore.cartella_di(c).mkdir(exist_ok=True)
motore.salva_impostazioni({"nome": "Studio di prova Esempio", "piva": "01234567897",
                           "cf": "PRVSTD70A01H501Z", "indirizzo": "Via Prova 1 - Roma",
                           "telefono": "000 000", "email": "prova@esempio.it"})
