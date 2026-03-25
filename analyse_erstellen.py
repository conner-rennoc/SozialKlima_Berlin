"""
analyse_erstellen.py
====================
Erzeugt analyse.geojson fuer die SozialKlima-Berlin-Website.

Eingabe:  rohdaten/*.geojson  (lokal, bereits vorhanden)
Ausgabe:  analyse.geojson     (im Repo-Root, EPSG:4326)

Ausgabefelder:
  PLR_ID, PLR_NAME, BEZ, hitze_pet, gruen_gvz, gruen_delta,
  sozial_index, belastung_score

Ausfuehren:
  python3 analyse_erstellen.py
"""

import os, json
import geopandas as gpd
import pandas as pd
import numpy as np

# ── Konfiguration ──────────────────────────────────────────────────────────────

ROHDATEN   = os.path.join(os.path.dirname(__file__), "rohdaten")
OUTPUT     = os.path.join(os.path.dirname(__file__), "analyse.geojson")

# Schwellenwerte fuer belastung_score (Perzentile, 0-100)
HITZE_PERZENTIL  = 75   # oberhalb → +1 Punkt
GRUEN_PERZENTIL  = 25   # unterhalb → +1 Punkt
SOZIAL_PERZENTIL = 40   # unterhalb → +1 Punkt (niedrigerer sdi_n = benachteiligter)

# Arbeits-CRS fuer Flaechenberechnungen (metrisch, Berlin)
CRS_WORK = "EPSG:25833"
CRS_OUT  = "EPSG:4326"

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def log(msg):
    print(f"  {msg}")


def flaechengewichteter_mittelwert(lor_gdf, daten_gdf, wert_feld):
    """
    Berechnet fuer jeden LOR-Planungsraum den flaechengewichteten Mittelwert
    des angegebenen Feldes aus daten_gdf.

    Gibt eine Series zurueck, indiziert nach LOR_ID.
    """
    log(f"Verschneide mit '{wert_feld}' ({len(daten_gdf)} Features)...")

    # Nur relevante Spalten behalten
    daten = daten_gdf[[wert_feld, "geometry"]].copy()
    daten = daten.dropna(subset=[wert_feld])
    daten[wert_feld] = pd.to_numeric(daten[wert_feld], errors="coerce")
    daten = daten.dropna(subset=[wert_feld])

    # Schnittmenge berechnen
    schnitt = gpd.overlay(
        lor_gdf[["PLR_ID", "geometry"]],
        daten,
        how="intersection",
        keep_geom_type=False,
    )

    if schnitt.empty:
        log(f"  WARNUNG: Keine Ueberschneidungen fuer '{wert_feld}' gefunden!")
        return pd.Series(dtype=float)

    # Schnittflaeche berechnen
    schnitt["_area"] = schnitt.geometry.area
    schnitt = schnitt[schnitt["_area"] > 0]

    # Flaechengewichteter Mittelwert je PLR_ID
    schnitt["_gewichtet"] = schnitt[wert_feld] * schnitt["_area"]
    agg = schnitt.groupby("PLR_ID").agg(
        _sumgew=("_gewichtet", "sum"),
        _sumarea=("_area", "sum"),
    )
    ergebnis = agg["_sumgew"] / agg["_sumarea"]
    log(f"  Ergebnis: {ergebnis.notna().sum()} von {len(lor_gdf)} LOR befuellt.")
    return ergebnis


# Bezirkscodes → Namen
BEZIRK_NAMEN = {
    "01": "Mitte",
    "02": "Friedrichshain-Kreuzberg",
    "03": "Pankow",
    "04": "Charlottenburg-Wilmersdorf",
    "05": "Spandau",
    "06": "Steglitz-Zehlendorf",
    "07": "Tempelhof-Schöneberg",
    "08": "Neukölln",
    "09": "Treptow-Köpenick",
    "10": "Marzahn-Hellersdorf",
    "11": "Lichtenberg",
    "12": "Reinickendorf",
}

# ── Hauptprogramm ──────────────────────────────────────────────────────────────

def main():
    print("\n=== analyse_erstellen.py ===\n")

    # 1. LOR laden
    print("[1/6] Lade LOR-Planungsraeume...")
    lor = gpd.read_file(os.path.join(ROHDATEN, "LOR_Planungsraeume.geojson"))
    lor = lor[["PLR_ID", "PLR_NAME", "BEZ", "geometry"]].copy()
    lor["PLR_ID"] = lor["PLR_ID"].astype(str)
    lor["BEZ_NAME"] = lor["BEZ"].astype(str).str.zfill(2).map(BEZIRK_NAMEN).fillna(lor["BEZ"].astype(str))
    # Datei deklariert EPSG:4326, Koordinaten sind aber metrisch (25833) → korrigieren
    lor = lor.set_crs("EPSG:25833", allow_override=True)
    log(f"{len(lor)} Planungsraeume geladen, CRS korrigiert auf EPSG:25833")

    # Ergebnis-DataFrame (ein Eintrag pro LOR)
    ergebnis = lor[["PLR_ID", "PLR_NAME", "BEZ", "BEZ_NAME"]].copy()

    # 2. PET laden und verschneiden
    print("\n[2/6] Lade und verschneide PET-Layer (Hitze)...")
    pet_dateien = {
        "Siedlungsflaechen": "Sidlungsflaechen_PET.geojson",
        "Verkehrsflaechen":  "Verkehrsflaechen_PET.geojson",
        "Gruen_Freiflaechen": "Gruen_Freiflaechen_PET.geojson",
    }
    pet_frames = []
    for label, datei in pet_dateien.items():
        log(f"Lade {label}...")
        gdf = gpd.read_file(os.path.join(ROHDATEN, datei))
        gdf = gdf[["pet14h", "geometry"]].copy()
        gdf = gdf.to_crs(CRS_WORK)
        pet_frames.append(gdf)

    log("Fasse alle PET-Flaechen zusammen...")
    pet_alle = pd.concat(pet_frames, ignore_index=True)
    pet_alle = gpd.GeoDataFrame(pet_alle, geometry="geometry", crs=CRS_WORK)

    pet_result = flaechengewichteter_mittelwert(lor, pet_alle, "pet14h")
    ergebnis["hitze_pet"] = ergebnis["PLR_ID"].map(pet_result)

    # 3. Gruenvolumen laden und verschneiden
    print("\n[3/6] Lade und verschneide Gruenvolumen...")
    gruen = gpd.read_file(os.path.join(ROHDATEN, "Gruenvolumen.geojson"))
    gruen = gruen[["flalle", "vegvola2020", "changegvz", "geometry"]].copy()
    gruen = gruen.to_crs(CRS_WORK)

    # vegvola2020 ist Gesamtvolumen in m³, flalle ist Polygonfläche in m².
    # GVZ pro Polygon (m³/m²) = vegvola2020 / flalle
    # Für jeden LOR: flächengewichteter Mittelwert von GVZ und changegvz.
    log("Berechne GVZ (m3/m2) und Delta je LOR...")
    gruen["gvz"] = (
        pd.to_numeric(gruen["vegvola2020"], errors="coerce") /
        pd.to_numeric(gruen["flalle"],      errors="coerce").replace(0, np.nan)
    )

    gvz_result   = flaechengewichteter_mittelwert(lor, gruen.rename(columns={"gvz": "_gvz"}), "_gvz")
    delta_result = flaechengewichteter_mittelwert(lor, gruen, "changegvz")
    ergebnis["gruen_gvz"]   = ergebnis["PLR_ID"].map(gvz_result)
    ergebnis["gruen_delta"] = ergebnis["PLR_ID"].map(delta_result)
    log(f"  gruen_gvz:   {ergebnis['gruen_gvz'].notna().sum()} LOR, Bereich {ergebnis['gruen_gvz'].min():.2f}–{ergebnis['gruen_gvz'].max():.2f} m3/m2")
    log(f"  gruen_delta: {ergebnis['gruen_delta'].notna().sum()} LOR, Bereich {ergebnis['gruen_delta'].min():.2f}–{ergebnis['gruen_delta'].max():.2f} m3/m2")

    # 4. MSS 2023 joinen (Attributjoin, kein Spatial Join)
    print("\n[4/6] Lade MSS 2023 und joine ueber PLR_ID...")
    mss = gpd.read_file(os.path.join(ROHDATEN, "Mss_2023_indizes.geojson"))
    mss["plr_id"] = mss["plr_id"].astype(str)
    # si_n ist der Statusindex (Skala 1–4); -9999 = NoData herausfiltern
    mss["si_n"] = pd.to_numeric(mss["si_n"], errors="coerce")
    mss.loc[mss["si_n"] < 0, "si_n"] = np.nan
    mss_lookup = mss.set_index("plr_id")["si_n"]

    ergebnis["sozial_index"] = ergebnis["PLR_ID"].map(mss_lookup)
    n_joined = ergebnis["sozial_index"].notna().sum()
    log(f"{n_joined} von {len(ergebnis)} LOR mit Sozialindex befuellt.")

    # 5. Mehrfachbelastungsindex berechnen
    print("\n[5/6] Berechne Mehrfachbelastungsindex...")

    h_schwelle = np.nanpercentile(ergebnis["hitze_pet"],   HITZE_PERZENTIL)
    g_schwelle = np.nanpercentile(ergebnis["gruen_gvz"],   GRUEN_PERZENTIL)
    s_schwelle = np.nanpercentile(ergebnis["sozial_index"], SOZIAL_PERZENTIL)

    log(f"Hitze-Schwelle  (>{HITZE_PERZENTIL}. Pzt.): {h_schwelle:.2f} °C")
    log(f"Gruen-Schwelle  (<{GRUEN_PERZENTIL}. Pzt.): {g_schwelle:.3f} m3/m2")
    log(f"Sozial-Schwelle (<{SOZIAL_PERZENTIL}. Pzt.): {s_schwelle:.2f} (si_n, 1=sehr niedrig, 4=hoch)")

    punkte_hitze  = (ergebnis["hitze_pet"]   > h_schwelle).astype(int)
    punkte_gruen  = (ergebnis["gruen_gvz"]   < g_schwelle).astype(int)
    punkte_sozial = (ergebnis["sozial_index"] < s_schwelle).astype(int)

    ergebnis["belastung_score"] = (punkte_hitze + punkte_gruen + punkte_sozial).where(
        ergebnis[["hitze_pet", "gruen_gvz", "sozial_index"]].notna().all(axis=1),
        other=pd.NA,
    ).astype("Int64")

    # Statistik ausgeben
    score_counts = ergebnis["belastung_score"].value_counts().sort_index()
    log("Verteilung belastung_score:")
    for score, count in score_counts.items():
        log(f"  Score {score}: {count} Planungsraeume")

    # 6. Als GeoJSON exportieren
    print("\n[6/6] Exportiere analyse.geojson...")

    # Geometrien aus LOR nehmen (EPSG:4326 fuer Leaflet)
    lor_wgs = lor.to_crs(CRS_OUT)
    export = lor_wgs.merge(
        ergebnis.drop(columns=["PLR_NAME", "BEZ"]),
        on="PLR_ID",
        how="left",
    )
    # BEZ_NAME aus ergebnis übernehmen (lor_wgs hat es nicht)
    export["BEZ_NAME"] = export["PLR_ID"].map(ergebnis.set_index("PLR_ID")["BEZ_NAME"])

    # Felder runden fuer kompaktere Dateigroe
    for col in ["hitze_pet", "gruen_gvz", "gruen_delta", "sozial_index"]:
        export[col] = export[col].round(3)

    # Spaltenreihenfolge
    spalten = ["PLR_ID", "PLR_NAME", "BEZ", "BEZ_NAME",
               "hitze_pet", "gruen_gvz", "gruen_delta",
               "sozial_index", "belastung_score", "geometry"]
    export = export[spalten]

    export.to_file(OUTPUT, driver="GeoJSON")

    # Groesse pruefen
    groesse_mb = os.path.getsize(OUTPUT) / 1_000_000
    log(f"Gespeichert: {OUTPUT}")
    log(f"Dateigroesse: {groesse_mb:.1f} MB")
    log(f"Features: {len(export)}")

    print("\nFertig. Naechster Schritt: analyse.geojson committen und pushen.")
    print("  git add analyse.geojson && git commit -m 'Add analyse.geojson'")


if __name__ == "__main__":
    main()
