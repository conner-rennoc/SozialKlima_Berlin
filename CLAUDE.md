# CLAUDE.md – Projektkontext für Claude Code

## Was ist das hier?

Ein Critical Mapping Projekt für einen Kurs an der TU Berlin (Institut für Stadt- und Regionalplanung). Es ist eine scrollbare, journalistische Website die räumliche Zusammenhänge zwischen Hitzebelastung, Grünvolumen und sozialer Ungleichheit in Berlin visualisiert.

**These:** Sozial benachteiligte Berliner Planungsräume sind systematisch stärker von Hitze betroffen und haben weniger Grün – und dieser Zusammenhang ist strukturell, nicht zufällig.

**Status:** Projekt abgeschlossen. Website live auf GitHub Pages.

---

## Repository-Struktur

```
/
├── index.html                  ← komplette Website (eine Datei, kein Build-System)
├── analyse.geojson             ← Analysedaten, 542 LOR, alle Felder (9 MB)
├── lor.geojson                 ← LOR-Geometrien Berlin (ODIS, EPSG:4326)
├── versiegelung.png            ← statische Karte: Versiegelungsgrad 2021
├── gruenversorgung.png         ← statische Karte: Grünversorgung + Parks + Wälder
├── analyse_erstellen.py        ← reproduzierbares Analyseskript
├── karten_rendern.py           ← reproduzierbares Karten-Rendering
├── tabelle_alle_faktoren.csv   ← alle 542 LOR, sortiert nach belastung_rang
├── tabelle_hitze_gruen.csv     ← alle 542 LOR, sortiert nach Hitze+Grün-Score
├── tabelle_bezirke.csv         ← alle 12 Bezirke aggregiert
├── tabelle_gruen_sozial.csv    ← alle 542 LOR, Grün~Sozial-Vergleich
├── CLAUDE.md                   ← dieser Kontext
└── README.md                   ← Anleitung für Menschen
```

**Wichtig:** Es gibt kein Build-System, kein npm, keine Abhängigkeiten. Alles ist eine einzige HTML-Datei. Die Rohdaten (`rohdaten/`, `gruenversorgung.geojson`) sind via `.gitignore` lokal gehalten.

---

## Tech Stack

- **Leaflet.js 1.9.4** (via CDN) – Kartenbibliothek
- **CartoDB Dark Tiles** – Basemap
- **Vanilla JS** – kein Framework
- **Google Fonts** – Playfair Display, Source Serif 4, DM Mono
- **GitHub Pages** – Hosting
- **geopandas, matplotlib, numpy, pandas** – Analyse & Rendering

---

## Datendateien

### analyse.geojson (vorhanden, vollständig)
542 Features, EPSG:4326, alle Felder befüllt.

| Feldname | Inhalt | Typ |
|---|---|---|
| `PLR_ID` | LOR-Schlüssel (8-stellig) | String |
| `PLR_NAME` | Name des Planungsraums | String |
| `BEZ` | Bezirkskürzel | String |
| `BEZ_NAME` | Bezirksname | String |
| `hitze_pet` | PET-Mittelwert 14 Uhr (°C) | Float |
| `gruen_gvz` | Grünvolumenzahl 2020 (m³/m²) | Float |
| `gruen_delta` | Δ GVZ 2010→2020 | Float |
| `esix_wert` | ESIx 2022 (kontinuierlich, höher = weniger belastet) | Float |
| `sozial_index` | MSS 2023 Gesamtindex (1–4, Ergänzung) | Float |
| `rang_hitze` | Perzentil-Rang PET (0–100, 100 = heißester) | Float |
| `rang_gruen` | Umgekehrter Rang GVZ (0–100, 100 = grünärmster) | Float |
| `rang_sozial` | Umgekehrter Rang ESIx (0–100, 100 = stärkste Belastung) | Float |
| `belastung_rang` | Summe rang_hitze + rang_gruen + rang_sozial (max. 300) | Float |
| `belastung_score_alt` | Alter MSS-basierter Score 0–3 (nur für Statistiken) | Int |

### lor.geojson
LOR-Planungsräume Berlin (542 PLR, Stand 2021), EPSG:4326.
Relevante Properties: `PLR_ID`, `PLR_NAME`, `BEZ_NAME`

---

## Konfigurationsblock (index.html)

```javascript
const CFG = {
  lorFile:           'lor.geojson',
  analyseFile:       'analyse.geojson',
  idField:           'PLR_ID',
  nameField:         'PLR_NAME',
  bezirkField:       'BEZ_NAME',
  hitzeFeld:         'hitze_pet',
  gruenFeld:         'gruen_gvz',
  sozialFeld:        'esix_wert',       // ESIx 2022, primärer Sozialindikator
  scoreFeld:         'belastung_score_alt',
  deltaFeld:         'gruen_delta',
  rangHitzeFeld:     'rang_hitze',
  rangGruenFeld:     'rang_gruen',
  rangSozialFeld:    'rang_sozial',
  belastungRangFeld: 'belastung_rang',
};
```

---

## Farbskalen (index.html)

- Hitze (PET): `#ffffb2` → `#d7191c` (hellgelb → dunkelrot)
- Grün (GVZ): `#edf8e9` → `#00441b` (hellgrün → dunkelgrün)
- Sozial (ESIx): `#f2e8ff` → `#3f007d` (hellviolett → dunkelviolett)
  - < −1,5: `#3f007d` — sehr starke Belastung
  - < −0,3: `#7b3fa3` — überdurchschnittliche Belastung
  - < +0,6: `#b894d4` — mittlerer Bereich
  - ≥ +0,6: `#f2e8ff` — geringe Belastung
- Mehrfachbelastung: 5-stufig, dynamisch auf Wertebereich normiert
- Dreifachbelastete LOR (alle 3 Ränge > 75): zusätzlich weiße Umrandung (weight 1.5)

---

## Analyselogik

### Flächengewichteter Mittelwert
Alle thematischen Layer werden via `flaechengewichteter_mittelwert()` in `analyse_erstellen.py` auf LOR-Ebene aggregiert (EPSG:25833 intern für metrische Flächen).

### ESIx-LOR-Mismatch
ESIx 2022 basiert auf LOR 2019 (448 PLR) → räumliche Verschneidung via `geopandas.overlay()` auf LOR 2021 (542 PLR). Alle 542 LOR haben einen `esix_wert`.

### Rang-basierte Normalisierung
Gewählt gegenüber Z-Scores, weil ESIx eine breitere Streuung als MSS hat und Z-Scores dadurch einzelne Faktoren übergewichten würden.

### Dreifachbelastung
Definition: `rang_hitze > 75 AND rang_gruen > 75 AND rang_sozial > 75` → **15 LOR**

---

## Zentrale Analyseergebnisse

| Kennzahl | Wert |
|---|---|
| Dreifachbelastete LOR | 15 |
| Bevölkerung in diesen LOR | ~115.000 |
| Wohnblockfläche ohne Grünversorgung | 28 % |
| PET-Spanne (min–max) | 13,4 °C (26,6–40,0 °C) |
| Ø Δ GVZ 2010→2020 | −0,30 m³/m² |
| Pearson r: Hitze+Grün ~ Sozial | 0,025 |
| Pearson r: rang_gruen ~ rang_sozial | 0,089 |
| Pearson r: gruen_gvz ~ esix_wert | 0,195 |

---

## Seitenstruktur

1. **Hero** – Vollbild-Karte, Titel, Autorennennung
2. **These** – Einleitungstext
3. **Mechanismus** – Versiegelung (statisch PNG) + Grünversorgung (statisch PNG) + Folge (PET)
4. **Daten** – Tabelle der verwendeten Datensätze mit "Was er misst"-Spalte
5. **Karte: Hitze** – Interaktive Choroplethenkarte (PET)
6. **Karte: Grün** – Interaktive Choroplethenkarte (GVZ)
7. **Karte: Sozial** – Interaktive Choroplethenkarte (ESIx)
8. **Karte: Mehrfachbelastung** – rang-basiert, Layer-Toggle, Dreifachbelastung weiß umrandet
9. **Erkenntnisse** – 115.000 / 28 % / 13,4 °C + Zwei-Typen-Text
10. **Fazit** – Methodenreflexion, Dynamiken, Grenzen, Planungsempfehlungen

---

## Stil & Tonalität

- **Editorial/journalistisch** – wie NYT oder Spiegel Online
- **Dunkel** – schwarzer Hintergrund für alle Karten-Blöcke
- **Papier-Töne** – `#f5f2eb` als Haupthintergrund
- Fonts: Playfair Display (Headlines), Source Serif 4 (Fließtext), DM Mono (Labels/Captions)
- Keine externen Abhängigkeiten außer CDN-Links im `<head>`

---

## Datenquellen (WFS-Referenz)

| Datensatz | URL |
|---|---|
| Klimaanalysekarten 2022 | `https://gdi.berlin.de/services/wfs/ua_stadtklima_2022` |
| Versiegelung 2021 | `https://gdi.berlin.de/services/wms/ua_versiegelung_2021` |
| Grünvolumen 2020 | `https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_05_09gruenvol2020` |
| MSS 2023 | `https://gdi.berlin.de/services/wfs/mss_2023` |
| LOR Planungsräume | `https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_lor_plr_2021` |
