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
YLIM = (5797000, 5839000)

BG = '#1a1814'          # Website-Hintergrundfarbe (--ink)
FIG_W, FIG_H = 12, 7.5  # ~1.6:1 Seitenverhältnis

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
    fig.savefig(pfad, dpi=120, bbox_inches='tight', pad_inches=0,
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
gdf_gv = gpd.read_file(os.path.join(ROOT, 'gruenversorgung.geojson'))
gdf_gv = gdf_gv.to_crs('EPSG:25833')

GV_COLORS = {
    'versorgter Bereich':          '#238b45',
    'unterversorgter Bereich':     '#74c476',
    'schlecht versorgter Bereich': '#c7e9c0',
    'nicht versorgter Bereich':    '#f2ede3',  # leicht wärmer als reines Weiß
}
gdf_gv['_color'] = gdf_gv['voeff_name'].map(GV_COLORS).fillna('#888888')

fig, ax = basis_figure()
gdf_gv.plot(
    ax=ax,
    color=gdf_gv['_color'],
    linewidth=0,
    edgecolor='none',
)
speichern(fig, os.path.join(ROOT, 'gruenversorgung.png'))

print("\nFertig. Nächster Schritt:")
print("  git add versiegelung.png gruenversorgung.png")
print("  git commit -m 'Add static map PNGs'")
