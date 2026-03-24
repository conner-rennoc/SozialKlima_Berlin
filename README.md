# SozialKlima_Berlin
Eine Website mit interaktiven Karten, welche die Zusammenhänge von Hitzebelastung und sozioökonomischen Gegebenheiten in bestimmten Gebieten Berlins erkundet.
[GitREADME1.md](https://github.com/user-attachments/files/26228342/GitREADME1.md)
# Stadtklima & Ungleichheit – Berlin
### Critical Mapping Projekt · TU Berlin

---

## Repository-Struktur

```
dein-repo/
├── index.html          ← die Website (bereits fertig)
├── lor.geojson         ← LOR-Geometrien (einmalig herunterladen, s.u.)
├── analyse.geojson     ← dein QGIS-Export (nach der Analyse erstellen)
└── README.md
```

---

## Schritt 1: LOR-Geodaten herunterladen

Gehe auf:
👉 https://daten.odis-berlin.de/de/dataset/lor_planungsgraeume_2021/

→ Klick auf **GeoJSON** → Datei speichern als `lor.geojson`  
→ Datei in den Repository-Ordner legen

---

## Schritt 2: QGIS-Analyse → analyse.geojson exportieren

Nach der Zonenstatistik-Analyse in QGIS:

1. Rechtsklick auf den LOR-Layer mit den Analysedaten
2. „Exportieren" → „Features speichern als…"
3. Format: **GeoJSON**
4. KBS: **EPSG:4326** (wichtig für Leaflet!)
5. Dateiname: `analyse.geojson`
6. In den Repository-Ordner legen

### Erwartete Attributnamen im GeoJSON

Die Website erwartet diese Feldnamen. Falls deine QGIS-Felder anders heißen, 
kannst du sie in `index.html` oben im `CFG`-Block anpassen.

| Feldname         | Inhalt                              | Typ    |
|------------------|-------------------------------------|--------|
| `PLR_ID`         | LOR-Schlüssel (8-stellig)           | String |
| `PLR_NAME`       | Name des Planungsraums              | String |
| `BEZ_NAME`       | Bezirksname                         | String |
| `hitze_pet`      | PET-Mittelwert (°C)                 | Float  |
| `gruen_gvz`      | Grünvolumenzahl (m³/m²)             | Float  |
| `gruen_delta`    | Δ GVZ 2010→2020                     | Float  |
| `sozial_index`   | MSS Gesamtindex 2023 (1–4)          | Float  |
| `sozial_2013`    | MSS Sozialindex 2013 (1–4)          | Float  |
| `sozial_2022`    | MSS Sozialindex 2022 (1–4)          | Float  |
| `belastung_score`| Mehrfachbelastung 0–3               | Int    |

### QGIS: Feldnamen anpassen (Feldrechner)

Falls deine Felder andere Namen haben, z.B. `mean_hitze` statt `hitze_pet`:

1. In QGIS: Layer → Attributtabelle öffnen
2. Feldrechner → neues Feld erstellen → `hitze_pet` = `"mean_hitze"`
3. Wiederholen für alle Felder

---

## Schritt 3: GitHub Pages aktivieren

1. Repository auf github.com erstellen
2. Alle drei Dateien hochladen (index.html, lor.geojson, analyse.geojson)
3. Settings → Pages → Branch: `main`, Ordner: `/ (root)` → Save
4. Nach ~2 Minuten ist die Seite unter `https://deinname.github.io/repo-name` erreichbar

---

## Feldwerte: Sozialindex (MSS)

Der MSS-Gesamtindex hat vier Ausprägungen:

| Wert | Bedeutung    |
|------|--------------|
| 1    | Sehr niedrig |
| 2    | Niedrig      |
| 3    | Mittel       |
| 4    | Hoch         |

---

## Lizenzhinweise

- LOR-Geodaten: Amt für Statistik Berlin-Brandenburg, CC BY 3.0 DE
- Umweltatlas-Daten: SenStadt Berlin, dl-zero-de/2.0
- MSS-Daten: SenStadt Berlin, dl-by-de/2.0 (Quellvermerk erforderlich)
