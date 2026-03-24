# CLAUDE.md – Projektkontext für Claude Code

## Was ist das hier?

Ein Critical Mapping Projekt für einen Kurs an der TU Berlin (Institut für Stadt- und Regionalplanung). Es ist eine scrollbare, journalistische Website die räumliche Zusammenhänge zwischen Hitzebelastung, Grünvolumen und sozialer Ungleichheit in Berlin visualisiert.

**These:** Sozial benachteiligte Berliner Planungsräume sind systematisch stärker von Hitze betroffen und haben weniger Grün – und dieser Zusammenhang hat sich durch Gentrifizierung zwischen 2013 und 2022 nicht verbessert.

---

## Repository-Struktur

```
/
├── index.html          ← komplette Website (eine Datei, kein Build-System)
├── lor.geojson         ← LOR-Planungsräume Berlin (Geometrien, von ODIS)
├── analyse.geojson     ← QGIS-Exportdatei mit Analysedaten (noch ausstehend)
├── README.md           ← Anleitung für Menschen
└── CLAUDE.md           ← dieser Kontext für Claude Code
```

**Wichtig:** Es gibt kein Build-System, kein npm, keine Abhängigkeiten. Alles ist eine einzige HTML-Datei mit eingebettetem CSS und JavaScript. Die Website läuft direkt als statische Seite auf GitHub Pages.

---

## Tech Stack

- **Leaflet.js 1.9.4** (via CDN) – Kartenbibliothek
- **CartoDB Dark Tiles** – Basemap
- **Vanilla JS** – kein Framework
- **Google Fonts** – Playfair Display, Source Serif 4, DM Mono
- **GitHub Pages** – Hosting

---

## Datendateien

### lor.geojson
LOR-Planungsräume Berlin (542 Planungsräume seit 2021).
- Quelle: ODIS Berlin / Amt für Statistik Berlin-Brandenburg
- KBS: EPSG:4326
- Relevante Properties: `PLR_ID` (8-stelliger Schlüssel), `PLR_NAME`, `BEZ_NAME`

### analyse.geojson (noch nicht vorhanden)
Wird aus QGIS exportiert nachdem die Zonenstatistik-Analyse abgeschlossen ist.
- KBS muss EPSG:4326 sein
- Muss folgende Felder enthalten (konfigurierbar im `CFG`-Block in index.html):

| Feldname         | Inhalt                              |
|------------------|-------------------------------------|
| `PLR_ID`         | LOR-Schlüssel (Join-Key zu lor.geojson) |
| `PLR_NAME`       | Name des Planungsraums              |
| `BEZ_NAME`       | Bezirksname                         |
| `hitze_pet`      | PET-Mittelwert (°C), Float          |
| `gruen_gvz`      | Grünvolumenzahl (m³/m²), Float      |
| `gruen_delta`    | Δ GVZ 2010→2020, Float              |
| `sozial_index`   | MSS Gesamtindex 2023 (1–4), Float   |
| `sozial_2013`    | MSS Sozialindex 2013 (1–4), Float   |
| `sozial_2022`    | MSS Sozialindex 2022 (1–4), Float   |
| `belastung_score`| Mehrfachbelastung 0–3, Integer      |

---

## Wie die Website funktioniert

### Datenladen (init-Funktion in index.html)
1. `lor.geojson` und `analyse.geojson` werden per `fetch()` geladen
2. `analyse.geojson` wird in ein Lookup-Objekt `{ PLR_ID: properties }` umgewandelt
3. Alle Leaflet-Layer werden aus `lor.geojson`-Geometrien aufgebaut
4. Farben werden aus den `analyse.geojson`-Werten via Lookup bestimmt

### Fehlerbehandlung
- Fehlt `lor.geojson` → alle Karten zeigen „Daten fehlen"-Banner
- Fehlt `analyse.geojson` → LOR-Geometrien werden grau angezeigt + Banner erklärt welche Felder fehlen
- Loading-Spinner bis Daten geladen oder Fehler aufgetreten

### Konfigurationsblock (oben in index.html)
```javascript
const CFG = {
  lorFile:     'lor.geojson',
  analyseFile: 'analyse.geojson',
  idField:     'PLR_ID',        // Join-Key
  hitzeFeld:   'hitze_pet',
  gruenFeld:   'gruen_gvz',
  // ... etc.
};
```
Wenn QGIS andere Feldnamen exportiert, nur hier anpassen.

### Farbskalen
- Hitze (PET): `#fee5d9` → `#cb181d` (hellrosa bis dunkelrot)
- Grün (GVZ): `#00441b` → `#edf8e9` (dunkelgrün bis hellgrün)
- Sozial (MSS): `#08306b` → `#eff3ff` (dunkelblau bis hellblau)
- Mehrfachbelastung: `#fef0d9` → `#b30000` (creme bis dunkelrot)

---

## Seitenstruktur (von oben nach unten)

1. **Hero** – Vollbild-Karte als Hintergrund, Titel
2. **These** – Einleitungstext
3. **Mechanismus** – Wie Versiegelung/Grün auf Hitze wirkt
4. **Daten** – Tabelle der verwendeten Datensätze
5. **Karte: Hitze** – Interaktive Choroplethenkarte
6. **Karte: Grün** – Interaktive Choroplethenkarte
7. **Karte: Sozial** – Interaktive Choroplethenkarte
8. **Karte: Mehrfachbelastung** – kombinierter Index mit Layer-Switcher
9. **Erkenntnisse** – drei Kennzahlen (auto-berechnet) + Text
10. **Fallbeispiele** – zwei Gebiete mit Zeit-Toggle (2013/2022)
    - Neukölln-Nord (Gentrifizierung)
    - Spandau-West (konstant belastet)
11. **Fazit** – planungsrelevante Schlussfolgerungen

---

## Häufige Aufgaben

### Feldnamen im CFG anpassen
Wenn QGIS-Export andere Feldnamen hat:
→ `CFG`-Block oben in index.html editieren

### Fallgebiete/Zoom-Koordinaten anpassen
```javascript
const NK = [52.477, 13.437]; // Neukölln-Nord [lat, lng]
const SP = [52.527, 13.196]; // Spandau-West
```
Zoom-Radius wird in `buildCase()` als `radiusDeg` übergeben (aktuell 0.032 ≈ 3.5 km).

### Neue Texte / Erkenntnisse eintragen
Die Erkenntnissektion (IDs `s1`, `s2`, `s3`) wird automatisch aus `analyse.geojson` berechnet wenn die Daten vorhanden sind. Statische Fallbeispiel-Texte sind direkt im HTML.

### Farben / Schwellenwerte ändern
Farbfunktionen `cHeat()`, `cGreen()`, `cSocial()`, `cScore()` in index.html anpassen.

---

## Was noch aussteht

- [ ] `analyse.geojson` aus QGIS exportieren und ins Repo laden
- [ ] CFG-Feldnamen ggf. an QGIS-Export anpassen
- [ ] Fallbeispiel-Texte nach Analyse-Ergebnissen konkretisieren
- [ ] Kennzahlen in der Erkenntnissektion prüfen
- [ ] Ggf. Zoom-Koordinaten der Fallgebiete feinjustieren

---

## Stil & Tonalität

- **Editorial/journalistisch** – wie NYT oder Spiegel Online
- **Dunkel** – schwarzer Hintergrund für alle Karten-Blöcke
- **Papier-Töne** – `#f5f2eb` als Haupthintergrund
- Fonts: Playfair Display (Headlines), Source Serif 4 (Fließtext), DM Mono (Labels/Captions)
- Keine externen Abhängigkeiten außer CDN-Links im `<head>`
- Kein Build-System – direkt editierbar

---

## Datenquellen (zur Referenz)

| Datensatz | WFS-URL |
|-----------|---------|
| Klimaanalysekarten 2022 | `https://gdi.berlin.de/services/wfs/ua_stadtklima_2022` |
| Klimaanalysekarten 2014 | `https://gdi.berlin.de/services/wfs/ua_stadtklima_2014` |
| Versiegelung 2021 | `https://gdi.berlin.de/services/wms/ua_versiegelung_2021` |
| Grünvolumen 2020 | `https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_05_09gruenvol2020` |
| MSS 2023 | `https://gdi.berlin.de/services/wfs/mss_2023` |
| MSS 2013 | `https://fbinter.stadt-berlin.de/fb/wfs/geometry/senstadt/re_Indizes_MSS2013` |
| LOR Planungsräume | `https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_lor_plr_2021` |
