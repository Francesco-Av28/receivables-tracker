# SCADENZIARIO — pagine HTML (template Jinja incorporati)
# Versione bianca: nessun logo, colore blu ardesia #4a687d,
# font Montserrat incluso nel pacchetto, tabelle compatte con ricerca e filtri, grafico mensile).

# titolo della scheda del browser per ogni pagina
TITOLI = {
    "dashboard": "Riepilogo", "smistamento": "Analisi fatture",
    "pagamenti": "Pagamenti", "fatture": "Fatture", "clienti": "Clienti", "scheda": "Scheda cliente", "impostazioni": "Impostazioni",
}

# icone del menu (SVG in linea, 16px, tratto = colore del testo)
_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
ICONE = {
    "riepilogo": _SVG.format('<path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="8"/><rect x="12" y="6" width="3" height="12"/><rect x="17" y="13" width="3" height="5"/>'),
    "analisi": _SVG.format('<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>'),
    "pagamenti": _SVG.format('<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/><path d="M6 15h4"/>'),
    "fatture": _SVG.format('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h8"/>'),
    "nuova": _SVG.format('<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>'),
    "clienti": _SVG.format('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>'),
    "scheda": _SVG.format('<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M6 16c0-1.7 1.3-3 3-3s3 1.3 3 3"/><path d="M14 9h4M14 13h4"/>'),
    "pdf": _SVG.format('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6M9 15l3 3 3-3"/>'),
    "report": _SVG.format('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6M9 15l3 3 3-3"/>'),
    "impostazioni": _SVG.format('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
    "cerca": _SVG.format('<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>'),
}

BASE = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ titoli.get(pagina, '') }} – Scadenziario</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%234a687d'/%3E%3Cpath d='M9 9h14v16H9z M12 14h8 M12 19h8' fill='none' stroke='white' stroke-width='2'/%3E%3C/svg%3E">
<style>
  @font-face { font-family: 'Montserrat'; src: url('/risorse/Montserrat.woff2') format('woff2');
               font-weight: 100 900; font-style: normal; font-display: swap; }
  :root { --blu: #4a687d; --blu-scuro: #3b5567; --blu-chiaro: #e6edf2; --blu-riga: #f2f5f8;
          --grigio: #8795a5; --grigio-testo: #5d6f80; --bordo: #d5dde5; --rosso: #c0392b;
          --rosso-chiaro: #fdecea; --verde: #1e8449; --verde-chiaro: #e8f6ee;
          --testo: #22313f; --sfondo: #f3f5f7; --serie-incassato: #2f6a9c; --serie-da: #c0392b; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { color-scheme: light; }
  body { font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif; background: var(--sfondo);
         color: var(--testo); font-size: 14px; }
  header { background: var(--blu); color: #fff; padding: 0 22px; display: flex; align-items: center;
           gap: 6px; flex-wrap: wrap; min-height: 62px; box-shadow: 0 2px 6px rgba(0,0,0,.15); }
  .marchio { display: flex; align-items: center; gap: 10px; margin-right: 12px; padding: 8px 0;
             text-decoration: none; color: #fff; }
  .marchio strong { font-size: 19px; font-weight: 700; letter-spacing: .3px; }
  .marchio span { font-size: 15px; font-weight: 600; letter-spacing: .5px; border-left: 1px solid rgba(255,255,255,.4);
                  padding-left: 12px; line-height: 1.1; }
  nav { display: flex; gap: 2px; flex-wrap: wrap; align-items: center; flex: 1; }
  nav a { color: #e3ebf1; text-decoration: none; font-size: 13px; font-weight: 500; padding: 8px 9px;
          border-radius: 7px; display: inline-flex; align-items: center; gap: 7px; }
  nav a svg { opacity: .85; }
  nav a:hover { background: rgba(255,255,255,.12); color: #fff; }
  nav a.attiva { background: #fff; color: var(--blu); font-weight: 600; }
  nav a.attiva svg { opacity: 1; }
  nav a.esci { margin-left: auto; }
  main { max-width: 1180px; margin: 22px auto; padding: 0 18px; }
  .card { background: #fff; border-radius: 10px; padding: 18px 22px; margin-bottom: 18px;
          box-shadow: 0 1px 3px rgba(34,49,63,.08); border: 1px solid #e6ebf0; }
  .schede { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
  .scheda { flex: 1; min-width: 170px; background: #fff; border-radius: 10px; padding: 14px 18px;
            border: 1px solid #e6ebf0; border-left: 5px solid var(--blu); box-shadow: 0 1px 3px rgba(34,49,63,.08); }
  .scheda.rossa { border-left-color: var(--rosso); }
  .scheda .numero { font-size: 24px; font-weight: 700; letter-spacing: -.3px; }
  .scheda.rossa .numero { color: var(--rosso); }
  .scheda .etichetta { color: var(--grigio-testo); font-size: 12px; margin-top: 3px; font-weight: 500; }
  h2 { font-size: 16px; margin-bottom: 12px; color: var(--blu-scuro); font-weight: 700; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; background: var(--blu-riga); padding: 7px 8px; color: var(--grigio-testo);
       border-bottom: 2px solid var(--bordo); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .3px; }
  td { padding: 5px 8px; border-bottom: 1px solid #edf1f5; vertical-align: middle; }
  tbody tr:hover td { background: #f7f9fb; }
  tr.scaduta td { color: var(--rosso); font-weight: 600; }
  .destra { text-align: right; white-space: nowrap; }
  td:first-child { white-space: nowrap; }
  .pill { display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 11.5px; font-weight: 600; }
  .pill.aperta { background: var(--rosso-chiaro); color: var(--rosso); }
  .pill.saldata { background: var(--verde-chiaro); color: var(--verde); }
  .bottone { display: inline-flex; align-items: center; gap: 6px; background: var(--blu); color: #fff; border: none;
             padding: 9px 18px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
             text-decoration: none; font-family: inherit; }
  .bottone:hover { background: var(--blu-scuro); }
  .bottone.verde { background: var(--verde); }
  .bottone.verde:hover { background: #27ae60; }
  .bottone.rosso { background: var(--rosso); }
  .bottone.grigio { background: var(--grigio); }
  .bottone.piccolo { padding: 4px 11px; font-size: 12.5px; }
  .avviso { padding: 11px 15px; border-radius: 8px; margin-bottom: 14px; font-size: 13.5px; font-weight: 500;
            border-left: 4px solid; }
  .avviso.ok { background: var(--verde-chiaro); color: var(--verde); border-color: var(--verde); }
  .avviso.errore { background: var(--rosso-chiaro); color: var(--rosso); border-color: var(--rosso); }
  form.riga { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
  label { display: block; font-size: 12px; color: var(--grigio-testo); margin-bottom: 4px; font-weight: 600; }
  input, select { padding: 8px 10px; border: 1px solid var(--bordo); border-radius: 7px; font-size: 13.5px;
                  background: #fff; font-family: inherit; color: var(--testo); }
  input:focus, select:focus { outline: 2px solid var(--blu); outline-offset: 1px; border-color: var(--blu); }
  .muto { color: var(--grigio-testo); font-size: 12.5px; }
  .vuoto { text-align: center; color: var(--grigio-testo); padding: 26px 0; }
  .strumenti { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
  .strumenti .cerca { position: relative; }
  .strumenti .cerca svg { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: var(--grigio); pointer-events: none; }
  .strumenti input[type=search] { padding-left: 30px; width: 240px; }
  .strumenti select { padding: 7px 9px; font-size: 13px; }
  .strumenti .conteggio { margin-left: auto; }
  tr[hidden] { display: none; }
  .grafico-testa { display: flex; gap: 18px; flex-wrap: wrap; align-items: baseline; margin-bottom: 6px; }
  .legenda { display: flex; gap: 14px; font-size: 12.5px; color: var(--grigio-testo); flex-wrap: wrap; }
  .legenda i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }
  .grafico-scroll { overflow-x: auto; }
  .grafico { width: 100%; min-width: 640px; height: auto; display: block; overflow: visible; }
  .grafico text { font-family: inherit; font-size: 11px; fill: var(--grigio-testo); }
  .grafico .griglia { stroke: #e3e8ee; stroke-width: 1; }
  .grafico .asse { stroke: var(--bordo); stroke-width: 1; }
  .grafico .valore { font-size: 11px; font-weight: 600; fill: var(--testo); text-anchor: middle; }
  .grafico .zona { fill: transparent; cursor: default; }
  .grafico g.mese:hover .zona { fill: rgba(74,104,125,.07); }
  .tooltip { position: fixed; pointer-events: none; background: #fff; color: var(--testo); border: 1px solid var(--bordo);
             border-radius: 8px; padding: 8px 11px; font-size: 12.5px; box-shadow: 0 4px 14px rgba(34,49,63,.16);
             z-index: 10; line-height: 1.5; }
  .tooltip b { display: block; margin-bottom: 2px; }
  .tooltip i { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
  .testa-scheda { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; }
  .testa-scheda h2 { font-size: 20px; margin-bottom: 4px; }
  .testa-scheda .azioni { display: flex; gap: 8px; flex-wrap: wrap; }
  .dati-cliente { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px 18px; margin-top: 10px; }
  .dati-cliente div { font-size: 13.5px; }
  .dati-cliente label { margin-bottom: 1px; }
  .apri-scheda { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; }
  .apri-scheda select { min-width: 300px; max-width: 100%; }
  td a.nome { color: var(--blu-scuro); font-weight: 600; text-decoration: none; }
  td a.nome:hover { text-decoration: underline; }
  @media (max-width: 860px) { header { padding: 6px 12px; } .marchio { width: 100%; justify-content: center; margin: 0; padding: 4px 0 6px; }
    .marchio span { display: none; } nav { justify-content: center; } nav a.esci { margin-left: 0; } main { padding: 0 10px; }
    .strumenti input[type=search] { width: 100%; } }
  @media print { header, .strumenti, .bottone, form { display: none !important; } body { background: #fff; } .card { box-shadow: none; border: none; } }
</style>
</head>
<body>
{% if sessione_attiva %}
<header>
  <a class="marchio" href="/"><strong>Scadenziario</strong>{% if nome_studio %}<span>{{ nome_studio }}</span>{% endif %}</a>
  <nav>
    <a href="/" class="{{ 'attiva' if pagina=='dashboard' }}">{{ icone.riepilogo|safe }} Riepilogo</a>
    <a href="/smistamento" class="{{ 'attiva' if pagina=='smistamento' }}">{{ icone.analisi|safe }} Analisi fatture</a>
    <a href="/pagamenti" class="{{ 'attiva' if pagina=='pagamenti' }}">{{ icone.pagamenti|safe }} Pagamenti</a>
    <a href="/fatture" class="{{ 'attiva' if pagina=='fatture' }}">{{ icone.fatture|safe }} Tutte le fatture</a>
    <a href="/fatture/nuova">{{ icone.nuova|safe }} Nuova fattura</a>
    <a href="/clienti" class="{{ 'attiva' if pagina in ('clienti', 'scheda') }}">{{ icone.clienti|safe }} Clienti</a>
    <a href="/report">{{ icone.report|safe }} Report PDF</a>
    <a href="/impostazioni" class="{{ 'attiva' if pagina=='impostazioni' }}">{{ icone.impostazioni|safe }} Impostazioni</a>
  </nav>
</header>
{% endif %}
<main>
{% with messaggi = get_flashed_messages(with_categories=true) %}
  {% for categoria, testo in messaggi %}
    <div class="avviso {{ categoria }}">{{ testo }}</div>
  {% endfor %}
{% endwith %}
{% block contenuto %}{% endblock %}
</main>
<script>
// ricerca istantanea e filtri sulle tabelle: i controlli hanno data-filtra="<id tabella>",
// i <select> anche data-campo="<attributo data-... della riga>"
function filtraTabella(id) {
  var tab = document.getElementById(id); if (!tab) return;
  var controlli = document.querySelectorAll('[data-filtra="' + id + '"]');
  var testo = '', selezioni = [];
  controlli.forEach(function (c) {
    if (c.tagName === 'SELECT') { if (c.value) selezioni.push([c.dataset.campo, c.value]); }
    else testo = c.value.trim().toLowerCase();
  });
  var visibili = 0;
  tab.querySelectorAll('tbody tr').forEach(function (r) {
    var ok = !testo || r.textContent.toLowerCase().indexOf(testo) !== -1;
    selezioni.forEach(function (s) { if (r.dataset[s[0]] !== s[1]) ok = false; });
    r.hidden = !ok; if (ok) visibili++;
  });
  var c = document.querySelector('[data-conteggio="' + id + '"]');
  if (c) c.textContent = visibili + ' di ' + tab.querySelectorAll('tbody tr').length;
}
document.querySelectorAll('[data-filtra]').forEach(function (c) {
  c.addEventListener('input', function () { filtraTabella(c.dataset.filtra); });
  c.addEventListener('change', function () { filtraTabella(c.dataset.filtra); });
});
document.querySelectorAll('table[id]').forEach(function (t) { filtraTabella(t.id); });
// tooltip del grafico
var tip = document.createElement('div'); tip.className = 'tooltip'; tip.hidden = true; document.body.appendChild(tip);
document.querySelectorAll('.grafico g.mese').forEach(function (g) {
  g.addEventListener('mousemove', function (e) {
    tip.innerHTML = g.dataset.tip; tip.hidden = false;
    var x = e.clientX + 14, y = e.clientY + 14;
    if (x + tip.offsetWidth > window.innerWidth - 8) x = e.clientX - tip.offsetWidth - 14;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  });
  g.addEventListener('mouseleave', function () { tip.hidden = true; });
});
</script>
</body>
</html>
"""

# barra con ricerca istantanea e filtri sopra una tabella
STRUMENTI = """
{% macro strumenti(id, stati=None, anni=None, situazioni=None, segnaposto='Cerca...') %}
<div class="strumenti">
  <div class="cerca">{{ icone.cerca|safe }}<input type="search" data-filtra="{{ id }}" placeholder="{{ segnaposto }}" aria-label="Cerca nella tabella"></div>
  {% if stati %}<select data-filtra="{{ id }}" data-campo="stato" aria-label="Stato">
    <option value="">Tutte</option>{% for s in stati %}<option>{{ s }}</option>{% endfor %}</select>{% endif %}
  {% if anni %}<select data-filtra="{{ id }}" data-campo="anno" aria-label="Anno">
    <option value="">Tutti gli anni</option>{% for a in anni %}<option>{{ a }}</option>{% endfor %}</select>{% endif %}
  {% if situazioni %}<select data-filtra="{{ id }}" data-campo="situazione" aria-label="Situazione">
    <option value="">Tutti i clienti</option>{% for v, et in situazioni %}<option value="{{ v }}">{{ et }}</option>{% endfor %}</select>{% endif %}
  <span class="muto conteggio" data-conteggio="{{ id }}"></span>
</div>
{% endmacro %}
"""

DASHBOARD = """
{% extends "base" %}
{% from "strumenti" import strumenti with context %}
{% block contenuto %}
<div class="card">
  <div class="grafico-testa">
    <h2 style="margin:0">Andamento ultimi 12 mesi</h2>
    <div class="legenda">
      <span><i style="background:var(--serie-incassato)"></i>Incassato &euro; {{ grafico.tot_incassato|euro }}</span>
      <span><i style="background:var(--serie-da)"></i>Da incassare &euro; {{ grafico.tot_da_incassare|euro }}</span>
      <span class="muto">Fatturato (altezza della barra) &euro; {{ grafico.tot_fatturato|euro }}</span>
    </div>
  </div>
  <div class="grafico-scroll"><svg class="grafico" viewBox="0 0 {{ grafico.larg }} {{ grafico.alt }}" role="img"
       aria-label="Barre mensili: incassato e da incassare per mese di emissione">
    {% for g in grafico.griglia %}
    <line class="griglia" x1="{{ grafico.x_inizio }}" x2="{{ grafico.x_fine }}" y1="{{ g.y }}" y2="{{ g.y }}"/>
    <text x="{{ grafico.x_inizio - 8 }}" y="{{ g.y + 4 }}" text-anchor="end">{{ g.testo }}</text>
    {% endfor %}
    <line class="asse" x1="{{ grafico.x_inizio }}" x2="{{ grafico.x_fine }}" y1="{{ grafico.y_base }}" y2="{{ grafico.y_base }}"/>
    {% for b in grafico.barre %}
    <g class="mese" data-tip="<b>{{ b.etichetta }} &middot; {{ b.n }} fattur{{ 'a' if b.n == 1 else 'e' }}</b><i style='background:var(--serie-incassato)'></i>Incassato &euro; {{ b.incassato|euro }}<br><i style='background:var(--serie-da)'></i>Da incassare &euro; {{ b.da_incassare|euro }}<br>Fatturato &euro; {{ b.fatturato|euro }}">
      <rect class="zona" x="{{ b.x - 8 }}" y="{{ 0 }}" width="{{ b.bw + 16 }}" height="{{ grafico.y_base }}"/>
      {% if b.h_inc >= 1 %}{% if b.path_inc %}<path d="{{ b.path_inc }}" fill="var(--serie-incassato)"/>
        {% else %}<rect x="{{ b.x }}" y="{{ b.y_inc }}" width="{{ b.bw }}" height="{{ b.h_inc }}" fill="var(--serie-incassato)"/>{% endif %}{% endif %}
      {% if b.path_da %}<path d="{{ b.path_da }}" fill="var(--serie-da)"/>{% endif %}
      {% if b.etichetta_valore and b.fatturato %}<text class="valore" x="{{ b.x_centro }}" y="{{ b.y_top - 6 }}">{{ b.fatturato|euro }}</text>{% endif %}
      <text x="{{ b.x_centro }}" y="{{ grafico.y_base + 18 }}" text-anchor="middle">{{ b.etichetta }}</text>
    </g>
    {% endfor %}
  </svg></div>
</div>

<div class="schede">
  <div class="scheda {{ 'rossa' if n_aperte }}"><div class="numero">&euro; {{ tot_aperto }}</div>
    <div class="etichetta">Crediti aperti</div></div>
  <div class="scheda"><div class="numero">{{ n_aperte }}</div>
    <div class="etichetta">Fatture da incassare</div></div>
  <div class="scheda {{ 'rossa' if scadute }}"><div class="numero">{{ scadute|length }}</div>
    <div class="etichetta">Fatture scadute</div></div>
  <div class="scheda"><div class="numero">{{ n_clienti }}</div>
    <div class="etichetta">Clienti in anagrafica</div></div>
</div>

{% if scadute %}
<div class="card">
  <h2>&#9888;&#65039; Fatture scadute (ordine alfabetico)</h2>
  {{ strumenti('tab-scadute', segnaposto='Cerca cliente o fattura...') }}
  <table id="tab-scadute">
    <thead><tr><th>Cliente</th><th>Fattura</th><th>Scadenza</th><th>Ritardo</th>
        <th class="destra">Residuo</th></tr></thead>
    <tbody>
    {% for f in scadute %}
    <tr class="scaduta"><td>{{ f.codice }} - {{ f.cliente }}</td>
      <td>FT {{ f.numero }}</td>
      <td>{{ f.scadenza.strftime('%d/%m/%Y') if f.scadenza }}</td>
      <td>{{ f.ritardo }} giorni</td>
      <td class="destra">&euro; {{ f.residuo|euro }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

<div class="card">
  <h2>Fatture aperte (ordine alfabetico)</h2>
  {% if aperte %}
  {{ strumenti('tab-aperte', anni=anni, segnaposto='Cerca cliente o fattura...') }}
  <table id="tab-aperte">
    <thead><tr><th>Cliente</th><th>Fattura</th><th>Data</th><th>Scadenza</th>
        <th class="destra">Totale</th><th class="destra">Residuo</th></tr></thead>
    <tbody>
    {% for f in aperte %}
    <tr {% if f.ritardo %}class="scaduta"{% endif %} data-anno="{{ f.data[-4:] }}">
      <td>{{ f.codice }} - {{ f.cliente }}</td><td>FT {{ f.numero }}</td>
      <td>{{ f.data }}</td>
      <td>{{ f.scadenza.strftime('%d/%m/%Y') if f.scadenza else '-' }}</td>
      <td class="destra">&euro; {{ f.totale|euro }}</td>
      <td class="destra">&euro; {{ f.residuo|euro }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}<div class="vuoto">Nessuna fattura aperta: tutto incassato &#127881;</div>{% endif %}
</div>
{% endblock %}
"""

SMISTAMENTO = """
{% extends "base" %}
{% block contenuto %}
<div class="card">
  <h2>Analisi fatture</h2>
  <p class="muto" style="margin-bottom:14px">
    Premi <b>Analizza</b>: l'app legge i PDF nuovi nella cartella <b>dati\\INBOX</b>,
    controlla le cartelle <b>dati\\CLIENTI</b> e segnala le fatture il cui PDF &egrave; stato tolto
    (verranno eliminate) e i PDF non registrati. Non cambia nulla senza la tua conferma.
  </p>
  <form method="post" action="/smistamento/analizza">
    <button class="bottone">{{ icone.analisi|safe }} Analizza ({{ n_file }} PDF nella INBOX)</button>
  </form>
</div>

{% if analisi %}
{% if analisi.esiti %}
<div class="card">
  <h2>Nuove fatture dalla INBOX</h2>
  <table>
    <thead><tr><th>File</th><th>Cliente</th><th>Fattura</th><th>Data</th><th>Scadenza</th>
        <th class="destra">Importo</th><th>Esito</th></tr></thead>
    <tbody>
    {% for e in analisi.esiti %}
    <tr>
      <td>{{ e.file }}</td>
      <td>{% if e.cliente %}{{ e.cliente.codice }} - {{ e.cliente.ragione_sociale }}
          {% elif e.nuovo_cliente %}<b>NUOVO:</b> {{ e.nuovo_cliente.ragione_sociale }}
          {% else %}-{% endif %}</td>
      <td>{{ 'FT ' + e.numero if e.numero else '-' }}</td>
      <td>{{ e.data.strftime('%d/%m/%Y') if e.data else '-' }}</td>
      <td>{{ e.scadenza.strftime('%d/%m/%Y') if e.scadenza else 'non trovata' }}</td>
      <td class="destra">{% if e.totale %}&euro; {{ e.totale|euro }}{% else %}-{% endif %}</td>
      <td>{% if e.ok %}<span class="pill saldata">pronta</span>
          {% else %}<span class="pill aperta">{{ e.errore }}</span>{% endif %}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  <p class="muto" style="margin-top:8px">I file con errori restano nella INBOX.</p>
</div>
{% endif %}

{% if analisi.mancanti %}
<div class="card">
  <h2>Fatture da eliminare &mdash; PDF tolto dalla cartella del cliente</h2>
  <table>
    <thead><tr><th>Cliente</th><th>Fattura</th><th>Data</th><th class="destra">Totale</th>
        <th class="destra">Residuo</th><th>File mancante</th><th>Pagamenti collegati</th></tr></thead>
    <tbody>
    {% for m in analisi.mancanti %}
    <tr>
      <td>{{ m.cliente.codice }} - {{ m.cliente.ragione_sociale }}</td>
      <td>FT {{ m.fattura.numero }}</td>
      <td>{{ m.fattura.data }}</td>
      <td class="destra">&euro; {{ m.fattura.totale|euro }}</td>
      <td class="destra">&euro; {{ m.fattura.residuo|euro }}</td>
      <td>{{ m.fattura.file }}</td>
      <td>{% if m.pagamenti %}
          {% for a in m.pagamenti %}&euro; {{ a.importo|euro }} del {{ a.data.strftime('%d/%m/%Y') if a.data else '?' }}
          &rarr; <b>verr&agrave; annullato</b>{% if not loop.last %}<br>{% endif %}{% endfor %}
          {% else %}nessuno{% endif %}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  <p class="muto" style="margin-top:8px">Se il PDF &egrave; stato tolto per sbaglio, rimettilo nella cartella
    del cliente e ripremi Analizza: la fattura non verr&agrave; eliminata.</p>
</div>
{% endif %}

{% if analisi.cartelle_mancanti %}
<div class="card">
  <h2>&#9888;&#65039; Cartelle cliente non trovate (nessuna eliminazione automatica)</h2>
  <table>
    <thead><tr><th>Cliente</th><th>Cartella attesa in dati\\CLIENTI</th><th>Fatture aperte coinvolte</th></tr></thead>
    <tbody>
    {% for cm in analisi.cartelle_mancanti %}
    <tr><td>{{ cm.cliente.codice }} - {{ cm.cliente.ragione_sociale }}</td>
      <td>{{ cm.cartella }}</td>
      <td>{% for f in cm.fatture %}FT {{ f.numero }} (&euro; {{ f.residuo|euro }}){% if not loop.last %}, {% endif %}{% endfor %}</td></tr>
    {% endfor %}
    </tbody>
  </table>
  <p class="muto" style="margin-top:8px">L'intera cartella del cliente &egrave; sparita: probabilmente &egrave; stata rinominata
    o spostata per sbaglio in Esplora file. Ripristinarla con il nome indicato e ripremere Analizza.
    Per eliminare davvero le fatture usare "Tutte le fatture".</p>
</div>
{% endif %}

{% if analisi.orfani %}
<div class="card">
  <h2>PDF nelle cartelle clienti non registrati (solo segnalazione)</h2>
  <table>
    <thead><tr><th>Cartella</th><th>File</th></tr></thead>
    <tbody>
    {% for o in analisi.orfani %}
    <tr><td>{{ o.cartella }}</td><td>{{ o.file }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
  <p class="muto" style="margin-top:8px">Per registrarli: spostali nella INBOX e ripremi Analizza,
    oppure usa "Nuova fattura".</p>
</div>
{% endif %}

{% if pronte or analisi.mancanti %}
<div class="card">
  <form method="post" action="/smistamento/conferma" style="display:inline"
        {% if analisi.mancanti %}onsubmit="return confirm('Confermi? Le fatture con PDF mancante verranno eliminate dall\\'app insieme ai pagamenti collegati.')"{% endif %}>
    <button class="bottone verde">&#9989; Conferma:
      {% if pronte %}registra {{ pronte }} {{ 'fattura' if pronte == 1 else 'fatture' }}{% endif %}
      {% if pronte and analisi.mancanti %} e {% endif %}
      {% if analisi.mancanti %}elimina {{ analisi.mancanti|length }} {{ 'fattura' if analisi.mancanti|length == 1 else 'fatture' }}{% endif %}
    </button>
  </form>
  {% if analisi.n_senza_pdf %}
  <span class="muto" style="margin-left:10px">{{ analisi.n_senza_pdf }} fatture senza PDF (inserite a mano o storiche) non vengono controllate.</span>
  {% endif %}
</div>
{% endif %}
{% endif %}
{% endblock %}
"""

PAGAMENTI = """
{% extends "base" %}
{% from "strumenti" import strumenti with context %}
{% block contenuto %}
<div class="card">
  <h2>Registra un pagamento</h2>
  <form method="post" action="/pagamenti/registra" class="riga">
    <div><label>Cliente</label>
      <select name="codice" required style="max-width:330px">
        <option value="">— scegli —</option>
        {% for c in clienti %}{% set s = situazione.get(c.codice) %}<option value="{{ c.codice }}">{{ c.codice }} - {{ c.ragione_sociale }}{% if s and s.da_incassare > 0 %} (da incassare &euro; {{ s.da_incassare|euro }}){% endif %}</option>{% endfor %}
      </select></div>
    <div><label>Importo &euro;</label><input name="importo" placeholder="es. 1.234,56" required style="width:120px"></div>
    <div><label>Data (vuota = oggi)</label><input name="data" placeholder="gg/mm/aaaa" style="width:120px"></div>
    <div><label>Fattura (vuota = più vecchia)</label><input name="fattura" placeholder="es. FPR 70/26" style="width:130px"></div>
    <div><label>Modalità</label>
      <select name="modalita"><option value="">-</option><option>Bonifico</option>
      <option>Contanti</option><option>Assegno</option><option>POS</option></select></div>
    <button class="bottone verde">Registra</button>
  </form>
  <p class="muto" style="margin-top:10px">Il PDF della fattura viene timbrato in rosso:
     ACCONTO se parziale, PAGATO quando è saldata. Si possono registrare solo pagamenti di
     fatture aperte: se il cliente non ha fatture aperte, o l'importo supera il dovuto,
     il pagamento viene rifiutato (smistare prima la fattura mancante dalla INBOX).</p>
</div>

<div class="card">
  <h2>Pagamenti registrati</h2>
  {% if acconti %}
  {{ strumenti('tab-pagamenti', anni=anni, segnaposto='Cerca cliente, fattura o importo...') }}
  <table id="tab-pagamenti">
    <thead><tr><th>Data</th><th>Cliente</th><th class="destra">Importo</th><th>Modalità</th>
        <th>Dettaglio</th><th></th></tr></thead>
    <tbody>
    {% for a in acconti %}
    <tr data-anno="{{ a.data.year if a.data }}"><td>{{ a.data.strftime('%d/%m/%Y') if a.data }}</td>
      <td>{{ a.codice }} - {{ nomi.get(a.codice, '?') }}</td>
      <td class="destra">&euro; {{ a.importo|euro }}</td>
      <td>{{ a.modalita }}</td><td class="muto">{{ a.nota }}</td>
      <td><form method="post" action="/pagamenti/elimina/{{ a.riga }}"
            onsubmit="return confirm('Annullare questo pagamento? I residui delle fatture verranno ripristinati e i timbri tolti dai PDF.')">
          <button class="bottone rosso piccolo">Annulla</button></form></td></tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}<div class="vuoto">Nessun pagamento registrato.</div>{% endif %}
</div>
{% endblock %}
"""

FATTURE = """
{% extends "base" %}
{% from "strumenti" import strumenti with context %}
{% block contenuto %}
<div class="card">
  <h2 style="display:flex;align-items:center;gap:16px">Tutte le fatture <span class="muto" style="font-weight:500">(ordine alfabetico per cliente)</span>
    <a class="bottone piccolo verde" href="/fatture/nuova">{{ icone.nuova|safe }} Nuova fattura a mano</a></h2>
  {% if fatture %}
  {{ strumenti('tab-fatture', stati=['Aperta', 'Saldata'], anni=anni, segnaposto='Cerca cliente o numero...') }}
  <table id="tab-fatture">
    <thead><tr><th>Cliente</th><th>Fattura</th><th>Data</th><th>Scadenza</th>
        <th class="destra">Totale</th><th class="destra">Residuo</th><th>Stato</th><th></th></tr></thead>
    <tbody>
    {% for f in fatture %}
    <tr {% if f.ritardo %}class="scaduta"{% endif %} data-stato="{{ f.stato }}" data-anno="{{ f.data[-4:] }}">
      <td>{{ f.codice }} - {{ f.cliente }}</td><td>FT {{ f.numero }}</td><td>{{ f.data }}</td>
      <td>{{ f.scadenza.strftime('%d/%m/%Y') if f.scadenza else '-' }}</td>
      <td class="destra">&euro; {{ f.totale|euro }}</td>
      <td class="destra">&euro; {{ f.residuo|euro }}</td>
      <td><span class="pill {{ 'aperta' if f.stato=='Aperta' else 'saldata' }}">{{ f.stato }}</span></td>
      <td style="white-space:nowrap">
        <a class="bottone piccolo" href="/fatture/modifica/{{ f.riga }}">Modifica</a>
        <form method="post" action="/fatture/elimina/{{ f.riga }}" style="display:inline"
          onsubmit="return confirm('Eliminare la fattura FT {{ f.numero }}? L\\'importo verrà tolto dal dovuto del cliente. Il PDF resta nella cartella.')">
          <button class="bottone rosso piccolo">Elimina</button></form></td></tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}<div class="vuoto">Nessuna fattura registrata.</div>{% endif %}
</div>
{% endblock %}
"""

FATTURA_MODIFICA = """
{% extends "base" %}
{% block contenuto %}
<div class="card" style="max-width:640px">
  <h2>Modifica fattura — {{ f.codice }} - {{ f.cliente }}</h2>
  <form method="post" class="riga">
    <div><label>Numero</label><input name="numero" value="{{ f.numero }}" required></div>
    <div><label>Data (gg/mm/aaaa)</label><input name="data" value="{{ f.data }}" required style="width:120px"></div>
    <div><label>Scadenza</label><input name="scadenza"
      value="{{ f.scadenza.strftime('%d/%m/%Y') if f.scadenza }}" style="width:120px"></div>
    <div><label>Totale &euro;</label><input name="totale" value="{{ f.totale|euro }}" required style="width:120px"></div>
    <button class="bottone verde">Salva</button>
    <a class="bottone grigio" href="/fatture">Annulla</a>
  </form>
  <p class="muto" style="margin-top:12px">Residuo attuale: &euro; {{ f.residuo|euro }} —
    se cambi il totale, il residuo e il dovuto del cliente si aggiustano di conseguenza.
    Se cambi il numero, viene aggiornato anche nei pagamenti collegati.</p>
</div>
{% endblock %}
"""

FATTURA_NUOVA = """
{% extends "base" %}
{% block contenuto %}
<div class="card" style="max-width:820px">
  <h2>Nuova fattura (inserimento a mano)</h2>
  <p class="muto" style="margin-bottom:14px">Per le fatture che non passano dalla INBOX (PDF scansionati,
     fatture senza PDF). Se il cliente non è in elenco, scegli <b>NUOVO CLIENTE</b> e compila i suoi dati:
     l'app crea la scheda in anagrafica e la sua cartella.</p>
  <form method="post" enctype="multipart/form-data">
    <div class="riga" style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;margin-bottom:14px">
      <div><label>Cliente</label>
        <select name="codice" id="codice" required style="max-width:360px" onchange="mostraNuovo()">
          <option value="">— scegli —</option>
          <option value="nuovo" {{ 'selected' if v.get('codice')=='nuovo' }}>&#10133; NUOVO CLIENTE (non in elenco)</option>
          {% for c in clienti %}<option value="{{ c.codice }}" {{ 'selected' if v.get('codice')==c.codice|string }}>{{ c.codice }} - {{ c.ragione_sociale }}{{ ' ' + c.nome if c.nome }}</option>{% endfor %}
        </select></div>
    </div>
    <div id="nuovo" class="riga" style="display:none;gap:12px;flex-wrap:wrap;align-items:flex-end;
         background:var(--blu-riga);padding:12px;border-radius:8px;margin-bottom:14px">
      <div><label>Ragione sociale / Cognome *</label><input name="nuovo_ragione_sociale" style="width:260px"
        value="{{ v.get('nuovo_ragione_sociale','') }}"></div>
      <div><label>Nome (persone fisiche)</label><input name="nuovo_nome" value="{{ v.get('nuovo_nome','') }}"></div>
      <div><label>Partita IVA</label><input name="nuovo_piva" style="width:130px" value="{{ v.get('nuovo_piva','') }}"></div>
      <div><label>Codice fiscale</label><input name="nuovo_cf" style="width:170px" value="{{ v.get('nuovo_cf','') }}"></div>
    </div>
    <div class="riga" style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end">
      <div><label>Numero fattura *</label><input name="numero" placeholder="es. FPR 82/26" required
        value="{{ v.get('numero','') }}" style="width:140px"></div>
      <div><label>Data (gg/mm/aaaa) *</label><input name="data" required value="{{ v.get('data', oggi) }}" style="width:120px"></div>
      <div><label>Scadenza</label><input name="scadenza" placeholder="gg/mm/aaaa" value="{{ v.get('scadenza','') }}" style="width:120px"></div>
      <div><label>Totale &euro; *</label><input name="totale" placeholder="es. 1.234,56" required
        value="{{ v.get('totale','') }}" style="width:120px"></div>
      <div><label>PDF della fattura (consigliato)</label><input type="file" name="pdf" accept="application/pdf"></div>
    </div>
    <div style="margin-top:16px">
      <button class="bottone verde">Registra fattura</button>
      <a class="bottone grigio" href="/fatture">Annulla</a>
    </div>
  </form>
  <p class="muto" style="margin-top:12px">Il PDF viene copiato nella cartella del cliente col nome standard
     (FT numero del data.pdf) e verrà timbrato ai pagamenti. Senza PDF la fattura esiste solo nei conti.</p>
</div>
<script>
function mostraNuovo() {
  document.getElementById('nuovo').style.display =
    document.getElementById('codice').value === 'nuovo' ? 'flex' : 'none';
}
mostraNuovo();
</script>
{% endblock %}
"""

CLIENTI = """
{% extends "base" %}
{% from "strumenti" import strumenti with context %}
{% block contenuto %}
<div class="card">
  <h2>{{ 'Modifica cliente' if in_modifica else 'Nuovo cliente' }}</h2>
  <form method="post" action="/clienti/salva" class="riga">
    <input type="hidden" name="codice" value="{{ in_modifica.codice if in_modifica }}">
    <div><label>Ragione sociale</label><input name="ragione_sociale" required style="width:280px"
      value="{{ in_modifica.ragione_sociale if in_modifica }}"></div>
    <div><label>Nome (persone fisiche)</label><input name="nome"
      value="{{ in_modifica.nome or '' if in_modifica }}"></div>
    <div><label>Partita IVA</label><input name="piva" style="width:130px"
      value="{{ in_modifica.piva if in_modifica }}"></div>
    <div><label>Codice fiscale</label><input name="cf" style="width:170px"
      value="{{ in_modifica.cf if in_modifica }}"></div>
    <div><label>Note</label><input name="note" value="{{ in_modifica.note if in_modifica }}"></div>
    <button class="bottone verde">Salva</button>
    {% if in_modifica %}<a class="bottone grigio" href="/clienti">Annulla</a>{% endif %}
  </form>
</div>

<div class="card">
  <h2>Scheda cliente</h2>
  <p class="muto" style="margin-bottom:10px">Apre la scheda di un solo cliente con tutti i suoi dati, le fatture, i pagamenti
     e i totali: da lì si scarica il PDF da inviare al cliente. Puoi anche cliccare sul nome nella tabella qui sotto.</p>
  <div class="apri-scheda">
    <div><label>Cliente</label>
      <select id="scegli-scheda" onchange="apriScheda()">
        <option value="">— scegli il cliente —</option>
        {% for c in clienti %}{% set s = situazione.get(c.codice) %}<option value="{{ c.codice }}">{{ c.codice }} - {{ c.ragione_sociale }}{{ ' ' + c.nome if c.nome }}{% if s and s.da_incassare > 0 %} (da incassare &euro; {{ s.da_incassare|euro }}){% endif %}</option>{% endfor %}
      </select></div>
    <button type="button" class="bottone" onclick="apriScheda()">{{ icone.scheda|safe }} Apri scheda</button>
  </div>
</div>
<script>
function apriScheda() {
  var v = document.getElementById('scegli-scheda').value;
  if (v) window.location.href = '/clienti/' + v;
}
</script>

<div class="card">
  <h2>Anagrafica ({{ clienti|length }} clienti) &mdash; da incassare in totale &euro; {{ tot_da_incassare|euro }}</h2>
  <p class="muto" style="margin-bottom:10px">Fatturato = fatture registrate; Incassato = pagamenti registrati;
     Da incassare = quanto resta aperto (in rosso). Un eventuale credito (pagato più del fatturato) è indicato accanto.</p>
  {{ strumenti('tab-clienti', situazioni=[('aperto', 'Con importi da incassare'), ('credito', 'Con credito'), ('ok', 'Senza importi aperti')], segnaposto='Cerca nome, P.IVA o codice fiscale...') }}
  <table id="tab-clienti">
    <thead><tr><th>Codice</th><th>Ragione sociale</th><th>P.IVA</th><th>Cod. fiscale</th>
        <th class="destra">Fatturato</th><th class="destra">Incassato</th>
        <th class="destra">Da incassare</th><th></th></tr></thead>
    <tbody>
    {% for c in clienti %}{% set s = situazione.get(c.codice) %}
    <tr data-situazione="{{ 'aperto' if s and s.da_incassare > 0 else ('credito' if s and s.credito > 0 else 'ok') }}">
      <td>{{ c.codice }}</td><td><a class="nome" href="/clienti/{{ c.codice }}" title="Apri la scheda">{{ c.ragione_sociale }}{{ ' ' + c.nome if c.nome }}</a></td>
      <td>{{ c.piva }}</td><td>{{ c.cf }}</td>
      <td class="destra">&euro; {{ (s.fatturato if s else 0)|euro }}</td>
      <td class="destra">&euro; {{ (s.incassato if s else 0)|euro }}</td>
      <td class="destra">{% if s and s.da_incassare > 0 %}<span class="pill aperta">&euro; {{ s.da_incassare|euro }}</span>
          {% else %}&euro; 0,00{% endif %}
          {% if s and s.credito > 0 %}<br><span class="muto">credito &euro; {{ s.credito|euro }}</span>{% endif %}</td>
      <td style="white-space:nowrap"><a class="bottone piccolo" href="/clienti/{{ c.codice }}">Scheda</a>
          <a class="bottone piccolo grigio" href="/clienti?modifica={{ c.codice }}">Modifica</a></td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
"""

SCHEDA_CLIENTE = """
{% extends "base" %}
{% from "strumenti" import strumenti with context %}
{% block contenuto %}
<div class="card">
  <div class="testa-scheda">
    <div>
      <p class="muto"><a href="/clienti" style="color:inherit">&larr; Tutti i clienti</a></p>
      <h2>{{ c.codice }} - {{ sc.nome_completo }}</h2>
      <div class="dati-cliente">
        <div><label>Partita IVA</label>{{ c.piva or '—' }}</div>
        <div><label>Codice fiscale</label>{{ c.cf or '—' }}</div>
        <div><label>Cartella documenti</label>dati\\CLIENTI\\{{ cartella }}</div>
        {% if c.note %}<div><label>Note</label>{{ c.note }}</div>{% endif %}
      </div>
    </div>
    <div class="azioni">
      <a class="bottone" href="/clienti/{{ c.codice }}/pdf">{{ icone.pdf|safe }} Scarica scheda PDF</a>
      <a class="bottone grigio" href="/clienti?modifica={{ c.codice }}">Modifica anagrafica</a>
      <a class="bottone grigio" href="/pagamenti">Registra pagamento</a>
    </div>
  </div>
  <p class="muto" style="margin-top:12px">Il PDF contiene l'intestazione dello studio, i dati del cliente, le fatture aperte con
     i giorni di ritardo, le fatture saldate, i pagamenti ricevuti e un invito al saldo: è pronto da allegare a una mail.
     Viene salvato anche in <b>dati\\SCHEDE CLIENTI</b>.</p>
</div>

<div class="schede">
  <div class="scheda"><div class="numero">{{ sc.n_fatture }}</div><div class="etichetta">Fatture registrate</div></div>
  <div class="scheda"><div class="numero">&euro; {{ sc.fatturato|euro }}</div><div class="etichetta">Fatturato</div></div>
  <div class="scheda"><div class="numero">&euro; {{ sc.incassato|euro }}</div><div class="etichetta">Incassato</div></div>
  <div class="scheda {{ 'rossa' if sc.da_incassare > 0 }}"><div class="numero">&euro; {{ sc.da_incassare|euro }}</div>
    <div class="etichetta">Da incassare ({{ sc.n_aperte }} aperte)</div></div>
  <div class="scheda {{ 'rossa' if sc.n_scadute }}"><div class="numero">{{ sc.n_scadute }}</div>
    <div class="etichetta">Scadute (&euro; {{ sc.tot_scaduto|euro }})</div></div>
  {% if sc.credito > 0 %}<div class="scheda"><div class="numero">&euro; {{ sc.credito|euro }}</div><div class="etichetta">Credito del cliente</div></div>{% endif %}
</div>

<div class="card">
  <h2>Fatture ({{ sc.n_fatture }})</h2>
  {% if sc.fatture %}
  {{ strumenti('tab-scheda-fatture', stati=['Aperta', 'Saldata'], anni=anni, segnaposto='Cerca numero o data...') }}
  <table id="tab-scheda-fatture">
    <thead><tr><th>Fattura</th><th>Data</th><th>Scadenza</th><th>Ritardo</th><th>Stato</th>
        <th class="destra">Totale</th><th class="destra">Pagato</th><th class="destra">Residuo</th><th></th></tr></thead>
    <tbody>
    {% for f in sc.fatture %}
    <tr class="{{ 'scaduta' if f.ritardo }}" data-stato="{{ f.stato }}" data-anno="{{ f.data[-4:] }}">
      <td>FT {{ f.numero }}</td><td>{{ f.data }}</td>
      <td>{{ f.scadenza.strftime('%d/%m/%Y') if f.scadenza else '—' }}</td>
      <td>{% if f.ritardo %}{{ f.ritardo }} gg{% else %}—{% endif %}</td>
      <td><span class="pill {{ f.stato|lower }}">{{ f.stato }}</span></td>
      <td class="destra">&euro; {{ f.totale|euro }}</td>
      <td class="destra">&euro; {{ (f.totale - f.residuo)|euro }}</td>
      <td class="destra">&euro; {{ f.residuo|euro }}</td>
      <td><a class="bottone piccolo grigio" href="/fatture/modifica/{{ f.riga }}">Modifica</a></td></tr>
    {% endfor %}
    </tbody>
    <tfoot><tr style="font-weight:700"><td colspan="5">TOTALE</td>
      <td class="destra">&euro; {{ sc.fatturato|euro }}</td>
      <td class="destra">&euro; {{ (sc.fatturato - sc.da_incassare)|euro }}</td>
      <td class="destra">&euro; {{ sc.da_incassare|euro }}</td><td></td></tr></tfoot>
  </table>
  {% else %}<p class="vuoto">Nessuna fattura registrata per questo cliente.</p>{% endif %}
</div>

<div class="card">
  <h2>Pagamenti ricevuti ({{ sc.pagamenti|length }}) &mdash; totale &euro; {{ sc.incassato|euro }}</h2>
  {% if sc.pagamenti %}
  <table id="tab-scheda-pagamenti">
    <thead><tr><th>Data</th><th class="destra">Importo</th><th>Modalità</th><th>Riferimento</th></tr></thead>
    <tbody>
    {% for a in sc.pagamenti %}
    <tr><td>{{ a.data.strftime('%d/%m/%Y') if a.data else '—' }}</td>
      <td class="destra">&euro; {{ a.importo|euro }}</td><td>{{ a.modalita or '—' }}</td>
      <td class="muto">{{ a.nota }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}<p class="vuoto">Nessun pagamento registrato.</p>{% endif %}
</div>
{% endblock %}
"""

IMPOSTAZIONI = """
{% extends "base" %}
{% block contenuto %}
<div class="card">
  <h2>Dati dello studio</h2>
  <p class="muto" style="margin-bottom:14px">Compaiono nell'intestazione del report PDF e delle schede cliente.
  P.IVA e codice fiscale servono anche all'<b>Analisi fatture</b>: nei PDF l'app li riconosce come quelli
  dello studio e prende gli altri come dati del cliente.</p>
  <form method="post" class="griglia-impostazioni">
    <label>Nome dello studio / ditta<input name="nome" value="{{ studio.nome }}"></label>
    <label>Partita IVA<input name="piva" value="{{ studio.piva }}"></label>
    <label>Codice fiscale<input name="cf" value="{{ studio.cf }}"></label>
    <label>Indirizzo<input name="indirizzo" value="{{ studio.indirizzo }}"></label>
    <label>Telefono<input name="telefono" value="{{ studio.telefono }}"></label>
    <label>E-mail<input name="email" value="{{ studio.email }}"></label>
    <label style="grid-column:1/-1">Testo che nelle fatture PDF precede il nome del cliente
      <span class="muto">(facoltativo: se vuoto si usa il nome dello studio; serve a leggere la ragione sociale dei clienti nuovi)</span>
      <input name="intestazione_fatture" value="{{ studio.intestazione_fatture }}"></label>
    <div style="grid-column:1/-1"><button class="bottone">Salva impostazioni</button></div>
  </form>
</div>
<div class="card">
  <h2>Dove sono i dati</h2>
  <p><code>{{ cartella_dati }}</code></p>
  <p class="muto" style="margin-top:8px">Per usare una cartella condivisa in rete (dati comuni a più PC) vedere il file LEGGIMI.txt.</p>
</div>
<style>
  .griglia-impostazioni { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px 18px; }
  .griglia-impostazioni label { display: flex; flex-direction: column; gap: 5px; font-weight: 600; font-size: 13px; }
  .griglia-impostazioni label .muto { font-weight: 400; }
  .griglia-impostazioni input { width: 100%; }
</style>
{% endblock %}
"""

PAGINE = {
    "base": BASE, "strumenti": STRUMENTI, "dashboard": DASHBOARD,
    "smistamento": SMISTAMENTO, "pagamenti": PAGAMENTI, "fatture": FATTURE,
    "fattura_modifica": FATTURA_MODIFICA, "fattura_nuova": FATTURA_NUOVA, "clienti": CLIENTI,
    "scheda_cliente": SCHEDA_CLIENTE, "impostazioni": IMPOSTAZIONI,
}
