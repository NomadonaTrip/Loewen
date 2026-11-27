"""Crop each before/after photo so its windrow trapezoid is centred, and bake
darker, softened surroundings around the trapezoid.

Reads the plain photos from images/windrows/web/modern/plain/ (never the served
files, so re-running never compounds) and the trapezoids from windrows.json
(plain 1500x1125 coords; back-left, back-right, front-right, front-left).
Writes windrow-<name>.webp (1500x1125) and windrow-<name>-750.webp. The trapezoid
is an invisible guide only; nothing is drawn on the photo.

Usage: python -I emphasize.py [name ...]   (no names = every entry in windrows.json)
Spec: docs/superpowers/specs/2026-11-27-windrow-overlay-design.md
"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H = 1500, 1125  # plain and output size
SMALL = (750, 562)
BLUR = 6          # px at 1500 wide
BRIGHTNESS = 0.60
SATURATION = 0.50
FEATHER = 40      # px, Gaussian radius of the mask edge
QUALITY = 90      # WebP; 80 lets the encoder blur the sharp area once the surroundings are soft
MIDDLE = 0.60     # the trapezoid must sit within the middle 60% of the crop height

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IMG = ROOT / "images/windrows/web/modern"


def centroid(poly):
    """Area centroid of a polygon."""
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    return cx / (3 * a), cy / (3 * a)


def crop_box(trap):
    """Largest 4:3 box inside the photo centred on the trapezoid's centroid.
    Cropping in only as much as centring needs; raises if the trapezoid then
    doesn't fit within the box's middle 60% height (or its width)."""
    cx, cy = centroid([tuple(p) for p in trap])
    half_h = min(cy, H - cy, cx * 3 / 4, (W - cx) * 3 / 4)
    k = math.floor(half_h / 3)            # box = 8k x 6k, exactly 4:3
    bw, bh = 8 * k, 6 * k
    left = min(max(round(cx - bw / 2), 0), W - bw)
    top = min(max(round(cy - bh / 2), 0), H - bh)
    box = (left, top, left + bw, top + bh)
    band = (top + bh * (1 - MIDDLE) / 2, top + bh * (1 + MIDDLE) / 2)
    if any(not (band[0] <= y <= band[1] and left <= x <= left + bw) for x, y in trap):
        raise ValueError(f"trapezoid {trap} does not fit the middle {MIDDLE:.0%} of crop {box}")
    return box


def to_output(trap, box):
    left, top, right, bottom = box
    sx, sy = W / (right - left), H / (bottom - top)
    return [(round((x - left) * sx), round((y - top) * sy)) for x, y in trap]


def emphasize(photo: Image.Image, polygon) -> Image.Image:
    """Keep the polygon sharp; blur, dim and desaturate everything else."""
    photo = photo.convert("RGB")
    mask = Image.new("L", photo.size, 0)
    pts = [tuple(p) for p in polygon]
    draw = ImageDraw.Draw(mask)
    draw.polygon(pts, fill=255)
    # grow the polygon by 2x the feather (a thick round-jointed outline) before
    # feathering, so the fade sits outside it and the polygon stays sharp
    draw.line(pts + [pts[0]], fill=255, width=4 * FEATHER, joint="curve")
    for x, y in pts:
        draw.ellipse((x - 2 * FEATHER, y - 2 * FEATHER, x + 2 * FEATHER, y + 2 * FEATHER), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER))
    soft = photo.filter(ImageFilter.GaussianBlur(BLUR))
    soft = ImageEnhance.Brightness(soft).enhance(BRIGHTNESS)
    soft = ImageEnhance.Color(soft).enhance(SATURATION)
    return Image.composite(photo, soft, mask)


def build(name, trap):
    """Crop, resize and darken one photo; write both sizes; return the trapezoid in output coords."""
    box = crop_box(trap)
    out_trap = to_output(trap, box)
    plain = Image.open(IMG / "plain" / f"windrow-{name}.webp").convert("RGB")
    out = emphasize(plain.crop(box).resize((W, H), Image.LANCZOS), out_trap)
    out.save(IMG / f"windrow-{name}.webp", quality=QUALITY, method=6)
    out.resize(SMALL, Image.LANCZOS).save(IMG / f"windrow-{name}-750.webp", quality=QUALITY, method=6)
    return out_trap


def main(names):
    windrows = json.loads((HERE / "windrows.json").read_text())
    for name in names or windrows:
        print("wrote", name, "crop", crop_box(windrows[name]), "trapezoid", build(name, windrows[name]))


if __name__ == "__main__":
    main(sys.argv[1:])
