#!/usr/bin/env python3
"""Generate a PDF sheet of ArUco markers (IDs 0-3) at several sizes to print at actual size."""
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

DPI = 300
SIZES_IN = [0.5, 0.75, 1.0, 1.5]
IDS = [0, 1, 2, 3]
OUT_PATH = Path(__file__).resolve().parent.parent.parent / "aruco_markers.pdf"
QUIET_ZONE_FRAC = 0.25  # white margin baked into each cut-out square, as a fraction of marker size
GAP = DPI // 2          # space between cut-out squares on the page

d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
page = Image.new("L", (int(8.5 * DPI), int(11 * DPI)), 255)
draw = ImageDraw.Draw(page)

x, y = DPI // 2, DPI // 2
row_height = 0
for size_in in SIZES_IN:
    px = int(size_in * DPI)
    quiet = int(px * QUIET_ZONE_FRAC)
    tile = px + 2 * quiet  # full cut-out size including white border
    draw.text((x, y), f'{size_in}"', fill=0)
    y += 20
    for marker_id in IDS:
        if x + tile > page.width - DPI // 2:
            x = DPI // 2
            y += row_height + GAP
            row_height = 0
            draw.text((x, y), f'{size_in}" (cont.)', fill=0)
            y += 20
        marker = cv2.aruco.generateImageMarker(d, marker_id, px)
        page.paste(Image.fromarray(marker), (x + quiet, y + quiet))
        draw.rectangle([x, y, x + tile, y + tile], outline=128)  # cut line
        draw.text((x, y + tile + 2), f"id{marker_id}", fill=0)
        x += tile + GAP
        row_height = max(row_height, tile)
    x = DPI // 2
    y += row_height + GAP + 20
    row_height = 0

page.save(OUT_PATH, "PDF", resolution=DPI)
print(f"Saved {OUT_PATH}")
