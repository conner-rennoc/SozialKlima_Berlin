"""
auswertung_erstellen.py
=======================
Erstellt alle Auswertungstabellen und berechnet Korrelationen
aus analyse.geojson.

Ausgabe:
  tabelle_alle_faktoren.csv   – alle 542 LOR, sortiert nach Gesamtbelastung
  tabelle_hitze_gruen.csv     – alle 542 LOR, sortiert nach Hitze+Grün-Score
  tabelle_bezirke.csv         – alle 12 Bezirke aggregiert
  tabelle_gruen_sozial.csv    – alle 542 LOR, Grün~Sozial-Vergleich

Ausführen:
  python3 auswertung_erstellen.py
"""

import json, csv, math, os

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, 'analyse.geojson'), encoding='utf-8') as f:
    features = json.load(f)['features']

props = [ft['properties'] for ft in features]
print(f"Geladen: {len(props)} Planungsräume")


# ── Hilfsfunktionen ────────────────────────────────────────────────────────

def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
    return num/den if den else None

def avg(vals):
    v = [x for x in vals if x is not None]
    return round(sum(v)/len(v), 1) if v else None

def write_csv(path, fieldnames, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  → {os.path.basename(path)} ({len(rows)} Zeilen)")


# ── 1. tabelle_alle_faktoren.csv ───────────────────────────────────────────
# Alle 542 LOR mit allen drei Faktoren, sortiert nach belastung_rang

rows = []
for p in props:
    rows.append({
        'PLR_NAME':      p.get('PLR_NAME', ''),
        'BEZ_NAME':      p.get('BEZ_NAME', ''),
        'rang_hitze':    p.get('rang_hitze'),
        'rang_gruen':    p.get('rang_gruen'),
        'rang_sozial':   p.get('rang_sozial'),
        'belastung_rang': p.get('belastung_rang'),
    })

rows.sort(key=lambda r: r['belastung_rang'] or 0, reverse=True)
write_csv(
    os.path.join(ROOT, 'tabelle_alle_faktoren.csv'),
    ['PLR_NAME','BEZ_NAME','rang_hitze','rang_gruen','rang_sozial','belastung_rang'],
    rows
)

# Dreifachbelastete LOR (alle drei Ränge > 75)
tripel = [r for r in rows
          if (r['rang_hitze'] or 0) > 75
          and (r['rang_gruen'] or 0) > 75
          and (r['rang_sozial'] or 0) > 75]
print(f"    Dreifachbelastete LOR: {len(tripel)}")
for r in tripel:
    print(f"      {r['PLR_NAME']:<35} {r['BEZ_NAME']:<25} Gesamt: {r['belastung_rang']}")


# ── 2. tabelle_hitze_gruen.csv ─────────────────────────────────────────────
# Alle 542 LOR, sortiert nach Hitze+Grün-Score; inkl. rang_sozial

rows_hg = []
for p in props:
    rh = p.get('rang_hitze')
    rg = p.get('rang_gruen')
    rs = p.get('rang_sozial')
    hgs = round(rh + rg, 1) if rh is not None and rg is not None else None
    rows_hg.append({
        'PLR_NAME':          p.get('PLR_NAME', ''),
        'BEZ_NAME':          p.get('BEZ_NAME', ''),
        'rang_hitze':        rh,
        'rang_gruen':        rg,
        'hitze_gruen_score': hgs,
        'rang_sozial':       rs,
    })

rows_hg.sort(key=lambda r: r['hitze_gruen_score'] or 0, reverse=True)
write_csv(
    os.path.join(ROOT, 'tabelle_hitze_gruen.csv'),
    ['PLR_NAME','BEZ_NAME','rang_hitze','rang_gruen','hitze_gruen_score','rang_sozial'],
    rows_hg
)

# Pearson: hitze_gruen_score ~ rang_sozial
pairs = [(r['hitze_gruen_score'], r['rang_sozial']) for r in rows_hg
         if r['hitze_gruen_score'] is not None and r['rang_sozial'] is not None]
r_hg_soz = pearson([p[0] for p in pairs], [p[1] for p in pairs])
print(f"    Pearson r (hitze_gruen_score ~ rang_sozial): {r_hg_soz:.4f}  (n={len(pairs)})")


# ── 3. tabelle_bezirke.csv ─────────────────────────────────────────────────
# Alle 12 Bezirke: Ø-Scores, PLR-Anzahl, Auszählung belasteter PLR

bezirke = {}
for p in props:
    bez = p.get('BEZ_NAME', '?')
    bezirke.setdefault(bez, []).append(p)

rows_bez = []
for bez, plr_list in bezirke.items():
    n = len(plr_list)
    rh   = avg([p.get('rang_hitze')  for p in plr_list])
    rg   = avg([p.get('rang_gruen')  for p in plr_list])
    rs   = avg([p.get('rang_sozial') for p in plr_list])
    hgs  = round(rh + rg, 1) if rh is not None and rg is not None else None
    rb   = avg([p.get('belastung_rang') for p in plr_list])

    # PLR mit Hitze+Grün beide >= 75 (Rang)
    hg_hoch = sum(
        1 for p in plr_list
        if (p.get('rang_hitze') or 0) >= 75 and (p.get('rang_gruen') or 0) >= 75
    )
    # Dreifachbelastet
    tripel_bez = sum(
        1 for p in plr_list
        if (p.get('rang_hitze') or 0) > 75
        and (p.get('rang_gruen') or 0) > 75
        and (p.get('rang_sozial') or 0) > 75
    )
    rows_bez.append({
        'BEZ_NAME':             bez,
        'anzahl_plr':           n,
        'avg_rang_hitze':       rh,
        'avg_rang_gruen':       rg,
        'avg_hitze_gruen_score': hgs,
        'avg_rang_sozial':      rs,
        'avg_belastung_rang':   rb,
        'plr_hitze_gruen_hoch': hg_hoch,
        'plr_dreifachbelastet': tripel_bez,
    })

rows_bez.sort(key=lambda r: r['avg_belastung_rang'] or 0, reverse=True)
write_csv(
    os.path.join(ROOT, 'tabelle_bezirke.csv'),
    ['BEZ_NAME','anzahl_plr','avg_rang_hitze','avg_rang_gruen',
     'avg_hitze_gruen_score','avg_rang_sozial','avg_belastung_rang',
     'plr_hitze_gruen_hoch','plr_dreifachbelastet'],
    rows_bez
)

print(f"    Bezirks-Ranking (Ø Gesamtbelastung):")
for r in rows_bez:
    print(f"      {r['BEZ_NAME']:<35} Ø {r['avg_belastung_rang']:>6}  3x: {r['plr_dreifachbelastet']}")


# ── 4. tabelle_gruen_sozial.csv ────────────────────────────────────────────
# Alle 542 LOR, sortiert nach rang_sozial; Grün-Rohwerte für Vergleich

rows_gs = []
for p in props:
    rows_gs.append({
        'PLR_NAME':    p.get('PLR_NAME', ''),
        'BEZ_NAME':    p.get('BEZ_NAME', ''),
        'gruen_gvz':   p.get('gruen_gvz'),
        'rang_gruen':  p.get('rang_gruen'),
        'esix_wert':   p.get('esix_wert'),
        'rang_sozial': p.get('rang_sozial'),
    })

rows_gs.sort(key=lambda r: r['rang_sozial'] or 0, reverse=True)
write_csv(
    os.path.join(ROOT, 'tabelle_gruen_sozial.csv'),
    ['PLR_NAME','BEZ_NAME','gruen_gvz','rang_gruen','esix_wert','rang_sozial'],
    rows_gs
)

# Pearson: rang_gruen ~ rang_sozial
pairs_rg = [(r['rang_gruen'], r['rang_sozial']) for r in rows_gs
            if r['rang_gruen'] is not None and r['rang_sozial'] is not None]
r_rg_rs = pearson([p[0] for p in pairs_rg], [p[1] for p in pairs_rg])

# Pearson: gruen_gvz (Rohwert) ~ esix_wert (Rohwert)
pairs_raw = [(r['gruen_gvz'], r['esix_wert']) for r in rows_gs
             if r['gruen_gvz'] is not None and r['esix_wert'] is not None]
r_raw = pearson([p[0] for p in pairs_raw], [p[1] for p in pairs_raw])

print(f"    Pearson r (rang_gruen ~ rang_sozial):  {r_rg_rs:.4f}  (n={len(pairs_rg)})")
print(f"    Pearson r (gruen_gvz  ~ esix_wert):   {r_raw:.4f}  (n={len(pairs_raw)})")


# ── Zusammenfassung ────────────────────────────────────────────────────────
print("\n── Zentrale Kennzahlen ───────────────────────────────────────────────")
pets = [p.get('hitze_pet') for p in props if p.get('hitze_pet') is not None]
print(f"  PET-Spanne: {min(pets):.1f} – {max(pets):.1f} °C  (Δ {max(pets)-min(pets):.1f} °C)")
deltas = [p.get('gruen_delta') for p in props if p.get('gruen_delta') is not None]
print(f"  Ø Δ GVZ 2010→2020: {sum(deltas)/len(deltas):.3f} m³/m²")
print(f"  Dreifachbelastete LOR: {len(tripel)}")
print(f"  Pearson r (H+G ~ Sozial):        {r_hg_soz:.4f}")
print(f"  Pearson r (rang_gruen ~ rang_soz): {r_rg_rs:.4f}")
print(f"  Pearson r (gruen_gvz ~ esix_wert): {r_raw:.4f}")
print("\nFertig.")
