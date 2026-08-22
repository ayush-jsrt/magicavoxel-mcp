"""Tiles per-view render PNGs into one labeled grid image, so the agent gets
a single image back instead of depending on multi-content-block tool
returns (an API surface not worth relying on — see docs/ARCHITECTURE.md)."""

import math

from PIL import Image, ImageDraw, ImageFont

LABEL_HEIGHT = 24


def compose_contact_sheet(view_paths: dict[str, str], out_path: str, columns: int = 3) -> None:
    if not view_paths:
        raise ValueError("view_paths must not be empty")

    tiles = {view: Image.open(path).convert("RGB") for view, path in view_paths.items()}
    tile_w = max(im.width for im in tiles.values())
    tile_h = max(im.height for im in tiles.values())

    views = list(tiles)
    columns = min(columns, len(views))
    rows = math.ceil(len(views) / columns)

    cell_w, cell_h = tile_w, tile_h + LABEL_HEIGHT
    sheet = Image.new("RGB", (cell_w * columns, cell_h * rows), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for i, view in enumerate(views):
        col, row = i % columns, i // columns
        x, y = col * cell_w, row * cell_h
        sheet.paste(tiles[view], (x, y))
        draw.text((x + 4, y + tile_h + 4), view, fill=(0, 0, 0), font=font)

    sheet.save(out_path)
