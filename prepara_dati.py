# Prepara la cartella "dati" VUOTA dell'app (Excel senza clienti né movimenti, INBOX,
# CLIENTI e le altre sottocartelle, config di base). Uso: python prepara_dati.py [cartella]
# Senza argomento azzera la cartella "dati" qui accanto (ATTENZIONE: cancella i dati presenti).
import shutil
import sys
from pathlib import Path

QUI = Path(__file__).parent
sys.path.insert(0, str(QUI))
import motore

DATI = Path(sys.argv[1]) if len(sys.argv) > 1 else QUI / "dati"
if DATI.exists():
    shutil.rmtree(DATI)
motore.inizializza_dati(DATI)
print(f"Cartella dati vuota pronta: {DATI}")
