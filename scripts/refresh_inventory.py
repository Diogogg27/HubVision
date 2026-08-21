# -*- coding: utf-8 -*-
"""Regenera .freebuff/pool_inventory.json varrendo as tres pastas de coleta."""
import os
import json
from PIL import Image

BASE = r"P:\LandingPage-PromptHub"
FOLDERS = [
    os.path.join(BASE, "PromptHub_coleta"),
    os.path.join(BASE, "PromptHub_coleta_fresh"),
    os.path.join(BASE, "PromptHub_coleta_fresh2"),
]
OUT = os.path.join(BASE, ".freebuff", "pool_inventory.json")

items = []
for col in FOLDERS:
    if not os.path.isdir(col):
        print("sem pasta:", col)
        continue
    for folder in sorted(os.listdir(col)):
        d = os.path.join(col, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            base = os.path.splitext(f)[0]
            txt_p = os.path.join(d, base + ".txt")
            if not os.path.exists(txt_p):
                continue
            jpg = os.path.join(d, f)
            try:
                im = Image.open(jpg)
                w, h = im.size
            except Exception:
                w = h = 0
            try:
                text = open(txt_p, encoding="utf-8", errors="ignore").read()
            except Exception:
                text = ""
            rel = os.path.relpath(col, BASE)
            items.append({
                "folder": folder,
                "file": base,
                "jpg": jpg,
                "w": w,
                "h": h,
                "dim": max(w, h),
                "text": text,
            })

json.dump(items, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("inventario:", len(items), "->", OUT)
