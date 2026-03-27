# Stadtklima & Ungleichheit – Berlin
### Critical Mapping Projekt · TU Berlin · Institut für Stadt- und Regionalplanung
**Conner Felix Defosse & Maximilian Felix Lemma · 2026**

Eine scrollbare, journalistische Web-Story, die räumliche Zusammenhänge zwischen Hitzebelastung, Grünversorgung und sozialer Ungleichheit in allen 542 Berliner Planungsräumen (LOR 2021) visualisiert.

🔗 **Live:** https://conner-rennoc.github.io/SozialKlima_Berlin

---

## These

Sozial benachteiligte Berliner Planungsräume sind systematisch stärker von Hitze betroffen und haben weniger Grün. Dieser Zusammenhang ist nicht zufällig – er ist das Ergebnis von Jahrzehnten Stadtplanung, die sozialen Wohnungsbau und klimatische Qualität selten zusammengedacht hat.

---

## Repository-Struktur

```
/
├── index.html                  ← komplette Website (eine Datei, kein Build-System)
├── analyse.geojson             ← Analysedaten, 542 LOR, alle berechneten Felder
├── lor.geojson                 ← LOR-Geometrien Berlin (ODIS, EPSG:4326)
├── versiegelung.png            ← statische Karte: Versiegelungsgrad 2021
├── gruenversorgung.png         ← statische Karte: Grünversorgung + Parks + Wälder
├── analyse_erstellen.py        ← reproduzierbares Analyseskript (Python)
├── karten_rendern.py           ← reproduzierbares Karten-Rendering (Python)
├── tabelle_alle_faktoren.csv   ← alle 542 LOR, sortiert nach Gesamtbelastung
├── tabelle_hitze_gruen.csv     ← alle 542 LOR, sortiert nach Hitze+Grün-Score
├── tabelle_bezirke.csv         ← alle 12 Bezirke aggregiert
├── tabelle_gruen_sozial.csv    ← alle 542 LOR, Grün~Sozial-Vergleich
├── CLAUDE.md                   ← technischer Projektkontext
└── README.md                   ← diese Datei
```

> **Rohdaten** (`rohdaten/`, `gruenversorgung.geojson`) sind lokal gehalten und nicht im Repo (`.gitignore`). Die Rohdaten stammen ausschließlich aus öffentlichen Berliner Geodiensten (siehe Datenquellen).

---

## Analyse reproduzieren

### Voraussetzungen
```bash
pip install geopandas pandas numpy matplotlib pillow
```

### Ausführen
```bash
python3 analyse_erstellen.py   # → analyse.geojson
python3 karten_rendern.py      # → versiegelung.png, gruenversorgung.png
```

Die Skripte erwarten die Rohdaten unter `rohdaten/`. Alle Schritte sind kommentiert und vollständig reproduzierbar.

---

## Methodik

### Analyseeinheit
542 LOR-Planungsräume Berlin (Stand 2021), aggregiert aus rasterförmigen und polygonalen Quelldaten via **flächengewichtetem Mittelwert** (area-weighted zonal statistics, EPSG:25833).

### Sozialindikator
Primär: **ESIx 2022** (Erwerbs- und Sozialindex, Gesundheits- & Sozialstrukturatlas Berlin) — kontinuierlicher Index aus 20 Indikatoren inkl. Wohnlage und Armutsrisiko.

ESIx basiert auf LOR 2019 (448 PLR) und wurde via **räumlicher Verschneidung** (`geopandas.overlay`) auf LOR 2021 (542 PLR) umgerechnet.

Ergänzend: **MSS 2023** (Monitoring Soziale Stadtentwicklung, SenStadt Berlin).

### Mehrfachbelastungsindex
Rang-basierte Normalisierung statt Z-Scores (robuster gegenüber schiefen Verteilungen):

| Feld | Berechnung | Bedeutung |
|---|---|---|
| `rang_hitze` | Perzentil-Rang PET (0–100) | 100 = heißester LOR |
| `rang_gruen` | Umgekehrter Perzentil-Rang GVZ (0–100) | 100 = grünärmster LOR |
| `rang_sozial` | Umgekehrter Perzentil-Rang ESIx (0–100) | 100 = stärkste Belastung |
| `belastung_rang` | Summe der drei Ränge (max. 300) | Mehrfachbelastungsindex |

**Dreifachbelastung:** alle drei Ränge > 75 → **15 Planungsräume** identifiziert.

---

## Zentrale Befunde

| Kennzahl | Wert |
|---|---|
| Dreifachbelastete Planungsräume | **15** |
| Einwohner*innen in diesen 15 LOR | **~115.000** |
| Wohnblockfläche ohne Grünversorgung | **28 %** |
| PET-Spanne heißester–kühlster Kiez | **13,4 °C** (26,6–40,0 °C) |
| Ø Δ Grünvolumen 2010→2020 | **−0,30 m³/m²** |
| Pearson r (Hitze+Grün ~ Sozial) | **0,025** (gesamtstädtisch schwach) |
| Pearson r (rang_gruen ~ rang_sozial) | **0,089** |
| Pearson r (gruen_gvz ~ esix_wert) | **0,195** |

Die schwachen gesamtstädtischen Korrelationen spiegeln zwei strukturell verschiedene Typen von Hitzeungerechtigkeit wider, die sich im Gesamtkoeffizienten teilweise aufheben:
1. **DDR-Großsiedlungen** (Marzahn-Hellersdorf, Lichtenberg, Spandau): klimatische Belastung eingebaut, soziale und klimatische Benachteiligung historisch gemeinsame Wurzel
2. **Innerstädtischer Gründerzeitgürtel** (Neukölln, Kreuzberg, Moabit, Wedding): Hitze durch Bebauungsdichte, soziale Belastung durch Verdrängung und Marktmechanismus

### Bezirks-Ranking (Gesamtbelastung, Ø belastung_rang)

| Rang | Bezirk | Ø Gesamt | Dreifachbelastete LOR |
|---|---|---|---|
| 1 | Neukölln | 191,2 | 5 |
| 2 | Marzahn-Hellersdorf | 178,4 | 3 |
| 3 | Mitte | 175,2 | 3 |
| 4 | Tempelhof-Schöneberg | 174,5 | 0 |
| 5 | Friedrichshain-Kreuzberg | 165,9 | 1 |
| … | … | … | … |
| 12 | Steglitz-Zehlendorf | 91,8 | 0 |

→ Vollständige Tabelle: `tabelle_bezirke.csv`

---

## Datenquellen & Lizenzen

| Datensatz | Jahr | Quelle | Lizenz |
|---|---|---|---|
| ESIx (Erwerbs- und Sozialindex) | 2022 | Gesundheits- & Sozialstrukturatlas Berlin | dl-zero-de/2.0 |
| MSS (Monitoring Soziale Stadtentwicklung) | 2023 | SenStadt Berlin | dl-zero-de/2.0 |
| Klimamodell Berlin – PET 14 Uhr | 2022 | Umweltatlas Berlin | dl-zero-de/2.0 |
| Versiegelung der Blockteilflächen | 2021 | Umweltatlas Berlin | dl-zero-de/2.0 |
| Grünvolumenzahl (inkl. Δ 2010→2020) | 2020 | Umweltatlas Berlin | dl-zero-de/2.0 |
| Versorgung mit wohnungsnahen Grünanlagen | 2020 | Umweltatlas Berlin | dl-zero-de/2.0 |
| Öffentliche Grünanlagen | aktuell | Umweltatlas Berlin | dl-zero-de/2.0 |
| Wald (Erholung) | aktuell | Umweltatlas Berlin | dl-zero-de/2.0 |
| LOR-Planungsräume 2021 | 2021 | Amt für Statistik Berlin-Brandenburg / ODIS | CC BY 3.0 DE |

---

## Tech Stack (Website)

- **Leaflet.js 1.9.4** (CDN) – interaktive Choroplethenkarten
- **CartoDB Dark Matter** – Basemap
- **Vanilla JS / HTML / CSS** – kein Framework, kein Build-System
- **GitHub Pages** – Hosting
- **geopandas + matplotlib** – Analyse & statische Karten
