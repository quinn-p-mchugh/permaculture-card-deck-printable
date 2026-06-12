#!/usr/bin/env python3
"""
build_cider_deck.py
====================
Converts a permaculture card PDF into a Cider-compatible database.json.

PDF layout assumption:
  - Odd pages  (1, 3, 5, …) = card FRONTS
  - Even pages (2, 4, 6, …) = card BACKS
  - Pages come in consecutive pairs: page 1 front / page 2 back = card 1

Output:
  - /tmp/cider_images/  ← individual PNGs named 1A.png, 1B.png, 2A.png, …
  - ./database.json     ← ready to import into https://oatear.github.io/cider/

Usage:
  python3 build_cider_deck.py [PDF_PATH] [OUTPUT_JSON] [--dpi N] [--max-width W]

Defaults:
  PDF_PATH     = Permaculture_Design_Deck_2022.pdf
  OUTPUT_JSON  = cider-database.json
  --dpi        = 150   (good balance of quality vs file size)
  --max-width  = 600   (downscale if wider; keeps aspect ratio)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path


# ─── Constants ────────────────────────────────────────────────────────────────

DECK_NAME        = "Permaculture Design Deck 2022"
CARD_WIDTH_PX    = 787.5    # Cider's standard card canvas width
CARD_HEIGHT_PX   = 1181.25   # Cider's standard card canvas height (2:3 ratio)
CARD_ASPECT      = "2:3"

FRONT_SUFFIX = "A"  # e.g. 1A = front of card 1
BACK_SUFFIX  = "B"  # e.g. 1B = back of card 1


# ─── PDF → PNG ────────────────────────────────────────────────────────────────

def render_pdf_to_images(pdf_path: str, out_dir: str, dpi: int, max_width: int) -> list[str]:
    """
    Render every page of the PDF to a PNG using pdftoppm.
    Returns sorted list of output PNG paths.

    Naming: pdftoppm writes <prefix>-000001.png, <prefix>-000002.png, …
    We rename them to 0001A.png, 0001B.png, 0002A.png, 0002B.png, … after rendering.
    """
    os.makedirs(out_dir, exist_ok=True)
    prefix = os.path.join(out_dir, "page")

    print(f"[1/3] Rendering PDF → PNG at {dpi} DPI …")
    cmd = [
        "pdftoppm",
        "-r", str(dpi),
        "-png",
        pdf_path,
        prefix,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"pdftoppm failed:\n{result.stderr}")

    # Collect and sort the raw output files
    raw_files = sorted(Path(out_dir).glob("page-*.png"))
    if not raw_files:
        sys.exit("pdftoppm produced no output files. Check the PDF path.")

    total_pages = len(raw_files)
    print(f"    Rendered {total_pages} pages.")

    if total_pages % 2 != 0:
        print(f"  WARNING: odd page count ({total_pages}). Last page has no back.")

    # Rename to card numbering: page-000001.png → 1A.png, page-000002.png → 1B.png, …
    renamed = []
    for i, raw in enumerate(raw_files):
        page_num = i + 1          # 1-based
        card_num = (page_num + 1) // 2   # card 1 = pages 1&2, card 2 = pages 3&4, …
        side     = FRONT_SUFFIX if page_num % 2 == 1 else BACK_SUFFIX
        new_name = os.path.join(out_dir, f"{card_num:04d}{side}.png")
        os.rename(raw, new_name)
        renamed.append(new_name)

    # Optional: downscale to max_width to keep base64 payload reasonable
    if max_width:
        _downscale_images(renamed, max_width)

    print(f"    Images saved to: {out_dir}")
    return renamed


def _downscale_images(paths: list[str], max_width: int):
    """Downscale PNGs in-place if wider than max_width, preserving aspect ratio."""
    try:
        from PIL import Image
    except ImportError:
        print("  (Pillow not installed — skipping downscale. pip install Pillow)")
        return

    print(f"    Downscaling images to max width {max_width}px …")
    for p in paths:
        img = Image.open(p)
        w, h = img.size
        if w > max_width:
            new_h = int(h * max_width / w)
            img = img.resize((max_width, new_h), Image.LANCZOS)
            img.save(p, "PNG", optimize=True)


# ─── Image → base64 ───────────────────────────────────────────────────────────

def image_to_base64(path: str) -> str:
    """Return base64-encoded PNG data (no data-URI prefix — Cider stores raw b64)."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


# ─── Build Cider database.json ────────────────────────────────────────────────

def build_database(image_paths: list[str]) -> dict:
    """
    Construct the full Dexie export structure that Cider expects.

    Tables used:
      decks           – one row, the deck name
      cardAttributes  – system + custom columns (name, count, front/back template)
      cardTemplates   – two templates: "Full Front" and "Full Back"
                        each is a full-bleed background-image using the card's asset
      assets          – one row per unique image (base64 PNG)
      cards           – one row per card pair (front + back)
      documents       – empty
      assetFolders    – empty
    """

    # ── sort image paths into pairs ──────────────────────────────────────────
    # Build dict: card_num → {"A": path, "B": path}
    pairs: dict[int, dict[str, str]] = {}
    for p in sorted(image_paths):
        fname = Path(p).stem          # e.g. "7A"
        card_num = int(fname[:-1])    # 7
        side     = fname[-1]          # "A" or "B"
        pairs.setdefault(card_num, {})[side] = p

    card_numbers = sorted(pairs.keys())
    print(f"[2/3] Building database for {len(card_numbers)} cards …")

    # ── IDs (Dexie auto-increments but we supply them explicitly) ─────────────
    DECK_ID          = 1
    TMPL_FRONT_ID    = 1
    TMPL_BACK_ID     = 2
    ATTR_NAME_ID     = 1   # system
    ATTR_COUNT_ID    = 2   # system
    ATTR_FRONT_ID    = 3   # system
    ATTR_BACK_ID     = 4   # system

    # ── Deck ──────────────────────────────────────────────────────────────────
    deck_rows = [{"id": DECK_ID, "name": DECK_NAME}]

    # ── Card templates ────────────────────────────────────────────────────────
    # Each template references the asset by card-specific name using the
    # Cider handlebars helper: {{index assets card.front}} or {{index assets card.back}}
    # where card.front / card.back hold the asset name for that card.
    front_html = '<div class="card"></div>'
    front_css  = """\
.card {
    width: 825px;
    height: 1125px;
    background-image: url({{index assets card.front}});
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}"""

    back_html = '<div class="card"></div>'
    back_css  = """\
.card {
    width: 825px;
    height: 1125px;
    background-image: url({{index assets card.back}});
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}"""

    template_rows = [
        {
            "id":          TMPL_FRONT_ID,
            "deckId":      DECK_ID,
            "name":        "Full Front",
            "description": "Full-bleed front image",
            "html":        front_html,
            "css":         front_css,
        },
        {
            "id":          TMPL_BACK_ID,
            "deckId":      DECK_ID,
            "name":        "Full Back",
            "description": "Full-bleed back image",
            "html":        back_html,
            "css":         back_css,
        },
    ]

    # ── Card attributes ───────────────────────────────────────────────────────
    # System attributes (Name, Count, Front Template, Back Template) are required.
    # We also add custom "front" and "back" attributes that hold the asset names.
    attr_rows = [
        {
            "id": ATTR_NAME_ID, "deckId": DECK_ID,
            "name": "Name", "type": "text",
            "description": "Card name", "options": [], "width": 135, "order": -4,
            "isSystem": True,
            "$types": {"options": "arrayNonindexKeys"},
        },
        {
            "id": ATTR_COUNT_ID, "deckId": DECK_ID,
            "name": "Count", "type": "numeric",
            "description": "How many of this card appear in the deck",
            "options": [], "width": 135, "order": -3,
            "isSystem": True,
            "$types": {"options": "arrayNonindexKeys"},
        },
        {
            "id": ATTR_FRONT_ID, "deckId": DECK_ID,
            "name": "Front Template", "type": "dropdown",
            "description": "The card's front template",
            "options": [], "width": 135, "order": -2,
            "isSystem": True,
            "$types": {"options": "arrayNonindexKeys"},
        },
        {
            "id": ATTR_BACK_ID, "deckId": DECK_ID,
            "name": "Back Template", "type": "dropdown",
            "description": "The card's back template",
            "options": [], "width": 135, "order": -1,
            "isSystem": True,
            "$types": {"options": "arrayNonindexKeys"},
        },
        # Custom attributes that templates reference
        {
            "id": 5, "deckId": DECK_ID,
            "name": "front", "type": "text",
            "description": "Asset name for the front image",
            "options": [], "width": 135, "order": 1,
            "$types": {"options": "arrayNonindexKeys"},
        },
        {
            "id": 6, "deckId": DECK_ID,
            "name": "back", "type": "text",
            "description": "Asset name for the back image",
            "options": [], "width": 135, "order": 2,
            "$types": {"options": "arrayNonindexKeys"},
        },
    ]

    # ── Assets + Cards ────────────────────────────────────────────────────────
    # Deduplicate assets by file content hash so repeated images (e.g. same
    # cover art used on multiple cards) only appear once in the JSON.
    import hashlib

    asset_rows   = []
    card_rows    = []
    hash_to_name = {}   # content_hash → asset_name already registered
    next_asset_id = 1

    for card_num in card_numbers:
        pair      = pairs[card_num]
        front_path = pair.get("A")
        back_path  = pair.get("B")

        # helper: register an image as an asset, deduplicating by hash
        def register_asset(path, label):
            nonlocal next_asset_id
            if path is None:
                return None

            with open(path, "rb") as f:
                data = f.read()
            h = hashlib.md5(data).hexdigest()

            if h in hash_to_name:
                return hash_to_name[h]   # reuse existing asset name

            asset_name = label  # e.g. "1A" or "7B"
            b64 = base64.b64encode(data).decode("ascii")
            asset_rows.append({
                "id":     next_asset_id,
                "file":   0,                 # 0 = no linked file record
                "name":   asset_name,
                "buffer": b64,
                "type":   "image/png",
                "$types": {
                    "file":   "undef",
                    "buffer": "arraybuffer",
                },
            })
            hash_to_name[h] = asset_name
            next_asset_id += 1
            return asset_name

        front_asset = register_asset(front_path, f"{card_num:04d}{FRONT_SUFFIX}")
        back_asset  = register_asset(back_path,  f"{card_num:04d}{BACK_SUFFIX}")

        card_rows.append({
            "id":                  card_num,
            "deckId":              DECK_ID,
            "name":                f"Card {card_num:04d}",
            "count":               "1",
            "frontCardTemplateId": TMPL_FRONT_ID,
            "backCardTemplateId":  TMPL_BACK_ID,
            "front":               front_asset or "",
            "back":                back_asset  or "",
            "$types": {},
        })

    print(f"    {len(card_rows)} card rows, {len(asset_rows)} unique image assets.")

    # ── Assemble Dexie export ─────────────────────────────────────────────────
    db = {
        "formatName":    "dexie",
        "formatVersion": 1,
        "data": {
            "databaseName":    "cider-db",
            "databaseVersion": 10,
            "tables": [
                {"name": "cards",          "schema": "++id,deckId,count,frontCardTemplateId,backCardTemplateId", "rowCount": len(card_rows)},
                {"name": "assets",         "schema": "++id,name,path",                                          "rowCount": len(asset_rows)},
                {"name": "cardTemplates",  "schema": "++id,deckId,name,description,html,css",                   "rowCount": len(template_rows)},
                {"name": "cardAttributes", "schema": "++id,deckId,name,[deckId+name],type,options,description,width,order", "rowCount": len(attr_rows)},
                {"name": "decks",          "schema": "++id,name",                                               "rowCount": len(deck_rows)},
                {"name": "documents",      "schema": "++id,name,mime,content",                                  "rowCount": 0},
                {"name": "assetFolders",   "schema": "++id,path",                                               "rowCount": 0},
            ],
            "data": [
                {"tableName": "cards",          "inbound": True, "rows": card_rows},
                {"tableName": "assets",         "inbound": True, "rows": asset_rows},
                {"tableName": "cardTemplates",  "inbound": True, "rows": template_rows},
                {"tableName": "cardAttributes", "inbound": True, "rows": attr_rows},
                {"tableName": "decks",          "inbound": True, "rows": deck_rows},
                {"tableName": "documents",      "inbound": True, "rows": []},
                {"tableName": "assetFolders",   "inbound": True, "rows": []},
            ],
        },
    }
    return db


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf",        nargs="?", default="Permaculture_Design_Deck_2022.pdf", help="Path to input PDF")
    parser.add_argument("output",     nargs="?", default="cider-database.json",                    help="Path to output JSON")
    parser.add_argument("--dpi",      type=int,  default=150,  help="Render DPI (default 150; source art ≈72 dpi so higher won't add sharpness)")
    parser.add_argument("--max-width",type=int,  default=600,  help="Downscale images to this max width in px (0 = no limit). Requires Pillow.")
    parser.add_argument("--images-dir", default="/tmp/cider_images", help="Where to store intermediate PNGs")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"PDF not found: {args.pdf}")

    # Step 1: render PDF pages to named PNGs
    image_paths = render_pdf_to_images(
        pdf_path  = args.pdf,
        out_dir   = args.images_dir,
        dpi       = args.dpi,
        max_width = args.max_width,
    )

    # Step 2: build the Cider database structure
    db = build_database(image_paths)

    # Step 3: write JSON
    print(f"[3/3] Writing {args.output} …")
    with open(args.output, "w") as f:
        json.dump(db, f, separators=(",", ":"))  # compact — saves ~20% vs pretty-print

    size_mb = os.path.getsize(args.output) / 1_048_576
    print(f"\n✓ Done. {args.output}  ({size_mb:.1f} MB)")
    print()
    print("Import into Cider:")
    print("  1. Open https://oatear.github.io/cider/")
    print("  2. Game menu → Import → select cider-database.json")
    print(f"  3. Deck '{DECK_NAME}' will appear with {len(db['data']['data'][0]['rows'])} cards.")
    print()
    print("Individual card images are in:", args.images_dir)
    print("  1A.png = front of card 1,  1B.png = back of card 1, etc.")


if __name__ == "__main__":
    main()
