"""
karten_rendern.py
=================
Rendert statische PNG-Karten für die Website aus lokalen GeoJSON-Dateien.

Ausgabe:
  versiegelung.png     ← Versiegelungsgrad 2021
  gruenversorgung.png  ← Versorgung mit wohnungsnahen Grünanlagen 2020

Ausführen:
  python3 karten_rendern.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os

ROOT = os.path.dirname(__file__)

# Berlin-Ausdehnung in EPSG:25833 (etwas Rand dazu)
XLIM = (366000, 418000)
YLIM = (5793000, 5843000)  # +4 km oben/unten → ~50 km hoch (vorher 42 km)

BG = '#1a1814'             # Website-Hintergrundfarbe (--ink)
FIG_W, FIG_H = 16, 13      # mehr Höhe → weniger Abschneiden

def basis_figure():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(XLIM)
    ax.set_ylim(YLIM)
    ax.set_aspect('equal')
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax

def speichern(fig, pfad):
    fig.savefig(pfad, dpi=150, bbox_inches='tight', pad_inches=0,
                facecolor=BG)
    plt.close(fig)
    # PNG-Kompression via Pillow wenn verfügbar
    try:
        from PIL import Image
        img = Image.open(pfad)
        img.save(pfad, optimize=True, compress_level=9)
    except ImportError:
        pass
    kb = os.path.getsize(pfad) / 1_000
    print(f"  Gespeichert: {pfad} ({kb:.0f} KB)")


# ── 1. Versiegelung ────────────────────────────────────────────────────────

print("[1/2] Rendere Versiegelung 2021...")
gdf_vs = gpd.read_file(os.path.join(ROOT, 'rohdaten', 'Versigelung Block.geojson'))
# Bereits in EPSG:25833 laut Inspektion — kein Reproject nötig

# Farbverlauf: grau → gelb → orange → dunkelrot (wie Hitzekarte)
cmap_vs = mcolors.LinearSegmentedColormap.from_list(
    'versiegelung',
    ['#d4cfc4', '#fecc5c', '#f97b2a', '#d7191c', '#7f0000']
)

fig, ax = basis_figure()
gdf_vs.plot(
    ax=ax,
    column='vg_2021',
    cmap=cmap_vs,
    vmin=0, vmax=100,
    linewidth=0,
    edgecolor='none',
)
speichern(fig, os.path.join(ROOT, 'versiegelung.png'))


# ── 2. Grünversorgung ──────────────────────────────────────────────────────

print("[2/2] Rendere Grünversorgung 2020...")

# LOR als Basis-Layer
gdf_lor = gpd.read_file(os.path.join(ROOT, 'lor.geojson'))
gdf_lor = gdf_lor.to_crs('EPSG:25833')

# Versorgungsgrad in Gelb-Abstufungen (dunkel = gut versorgt, hell = schlecht)
gdf_gv = gpd.read_file(os.path.join(ROOT, 'gruenversorgung.geojson'))
gdf_gv = gdf_gv.to_crs('EPSG:25833')

GV_COLORS = {
    'versorgter Bereich':          '#c47d00',  # sattes Amber (beste Versorgung)
    'unterversorgter Bereich':     '#e8b014',  # mittleres Gelb
    'schlecht versorgter Bereich': '#f5d87a',  # helles Gelb
    'nicht versorgter Bereich':    '#fef0c0',  # sehr helles Creme-Gelb
}
gdf_gv['_color'] = gdf_gv['voeff_name'].map(GV_COLORS).fillna('#888888')

# Parks und Wälder als Overlay
gdf_parks = gpd.read_file(os.path.join(ROOT, 'rohdaten', 'öffentliche grünanlagen.geojson'))
gdf_parks = gdf_parks.to_crs('EPSG:25833')

gdf_wald = gpd.read_file(os.path.join(ROOT, 'rohdaten', 'Wald (erholung).geojson'))
# Wald liegt bereits in EPSG:25833

fig, ax = basis_figure()
# 1) LOR als neutrale Basis
gdf_lor.plot(ax=ax, color='#3a3630', linewidth=0, edgecolor='none')
# 2) Versorgungsgrad (gelbe Abstufungen)
gdf_gv.plot(ax=ax, color=gdf_gv['_color'], linewidth=0, edgecolor='none')
# 3) Parks (mittleres Grün)
gdf_parks.plot(ax=ax, color='#3a8c4e', linewidth=0, edgecolor='none')
# 4) Wälder (dunkles Grün)
gdf_wald.plot(ax=ax, color='#1a5230', linewidth=0, edgecolor='none')
speichern(fig, os.path.join(ROOT, 'gruenversorgung.png'))

print("\nFertig. Nächster Schritt:")
print("  git add versiegelung.png gruenversorgung.png")
print("  git commit -m 'Add static map PNGs'")
