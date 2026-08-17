#!/usr/bin/env python3
"""Build a before/after strip per demo: the two references on the left, the result on the right."""
from PIL import Image
import os

DEMOS = [("can", "can_scene-s42", "can_label-s84"),
         ("gable", "gable_scene-s77", "gable_mural-s79"),
         ("neon", "storefront_scene-s42", "neon_sign-s42"),
         ("book", "book_scene-s77", "book_cover-s42"),
         ("tattoo", "arm_scene-s77", "tattoo_flash-s42")]
H = 420
os.makedirs("sheets", exist_ok=True)

def fit(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)

for name, scene, art in DEMOS:
    refs = [fit(Image.open(f"refs/{scene}.png").convert("RGB"), H // 2 - 4),
            fit(Image.open(f"refs/{art}.png").convert("RGB"), H // 2 - 4)]
    out = fit(Image.open(f"out/{name}.png").convert("RGB"), H)
    left = max(r.width for r in refs)
    sheet = Image.new("RGB", (left + 16 + out.width, H), "white")
    sheet.paste(refs[0], (0, 0))
    sheet.paste(refs[1], (0, H // 2 + 4))
    sheet.paste(out, (left + 16, 0))
    sheet.save(f"sheets/{name}.png")
    print(f"sheets/{name}.png  {sheet.size}")
