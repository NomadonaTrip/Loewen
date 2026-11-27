"""Checks for the centred crops and baked darkening (the windrow spotlight)
(docs/superpowers/specs/2026-11-27-windrow-overlay-design.md).

Run: python -I tools/windrow-emphasis/test_emphasize.py   (needs Pillow)
Every photo named in windrows.json is checked; EXPECTED lists the ones that must exist.
windrows.json: {"<key>-<side>": [[x,y] x4]} trapezoid corners in plain 1500x1125 coords
(back-left, back-right, front-right, front-left). The trapezoid in the cropped output's
own 1500x1125 coords comes from emphasize.crop_box / emphasize.to_output.
"""
import hashlib, io, json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IMG = ROOT / "images/windrows/web/modern"
PLAIN = IMG / "plain"
EXPECTED = [f"{k}-{s}" for k in "gjkbdei" for s in ("before", "after")]  # hero g + six gallery pairs
LIME = (217, 245, 139)
failed = 0


def check(name, ok, detail=""):
    global failed
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  ({detail})"))
    failed += not ok


def poly_mask(poly, grow=0):
    """Polygon mask grown (grow > 0) or shrunk (grow < 0) by |grow| px.
    Uses a thick round-jointed outline, which is fast; rank filters this wide
    take minutes in Pillow."""
    pts = [tuple(p) for p in poly]
    m = Image.new("L", (1500, 1125), 0)
    d = ImageDraw.Draw(m)
    d.polygon(pts, fill=255)
    if grow:
        fill = 255 if grow > 0 else 0
        d.line(pts + [pts[0]], fill=fill, width=2 * abs(grow), joint="curve")
        for x, y in pts:
            d.ellipse((x - abs(grow), y - abs(grow), x + abs(grow), y + abs(grow)), fill=fill)
    return m


def centroid(poly):
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    return cx / (3 * a), cy / (3 * a)


def stats(im, m):
    return ImageStat.Stat(im.convert("L"), m).mean[0], ImageStat.Stat(im.convert("HSV").split()[1], m).mean[0]


wfile = HERE / "windrows.json"
windrows = json.loads(wfile.read_text()) if wfile.exists() else {}
check("windrows.json exists", wfile.exists())
check("old strips.json removed", not (HERE / "strips.json").exists())
check("overlay data file removed", not (ROOT / "js/windrow-overlay-data.js").exists())
check("overlay script removed", not (ROOT / "js/windrow-overlay.js").exists())

emph = None
if (HERE / "emphasize.py").exists():
    sys.path.insert(0, str(HERE))
    import emphasize as emph

sums = {}
if (PLAIN / "SHA256SUMS").exists():
    for line in (PLAIN / "SHA256SUMS").read_text().split("\n"):
        if line.strip():
            h, n = line.split(maxsplit=1)
            sums[n.strip()] = h

for name in EXPECTED:
    t = windrows.get(name)
    check(f"{name}: trapezoid defined (4 corners)", isinstance(t, list) and len(t) == 4, "missing or wrong shape")

for name in sorted(set(EXPECTED) | set(windrows)):
    trap = windrows.get(name)
    if not (isinstance(trap, list) and len(trap) == 4 and emph):
        continue
    try:
        box = emph.crop_box(trap)
    except ValueError as e:
        check(f"{name}: crop rule satisfied", False, str(e))
        continue
    check(f"{name}: crop at least 50% of photo width ({box[2] - box[0]} px)", box[2] - box[0] >= 750, box)
    out_trap = emph.to_output(trap, box)
    fn = f"windrow-{name}.webp"
    plain_path, out_path, small_path = PLAIN / fn, IMG / fn, IMG / f"windrow-{name}-750.webp"
    if not plain_path.exists():
        check(f"{name}: plain copy kept", False, f"missing {plain_path.name}")
        continue
    check(f"{name}: plain copy unchanged since it was saved",
          sums.get(fn) == hashlib.sha256(plain_path.read_bytes()).hexdigest(), "checksum mismatch or missing")
    out = Image.open(out_path).convert("RGB")
    check(f"{name}: 1500 size", out.size == (1500, 1125), out.size)
    check(f"{name}: 750 size", Image.open(small_path).size == (750, 562), Image.open(small_path).size)

    # trapezoid centred, and within the middle 60% of the height
    out_trap = [tuple(p) for p in out_trap]
    cx, cy = centroid(out_trap)
    check(f"{name}: trapezoid centred ({cx:.0f}, {cy:.0f})", math.dist((cx, cy), (750, 562)) <= 8, f"({cx:.1f}, {cy:.1f})")
    ys = [y for _, y in out_trap]
    check(f"{name}: trapezoid within y 225-900 ({min(ys)}-{max(ys)})", 225 <= min(ys) and max(ys) <= 900, f"{min(ys)}-{max(ys)}")

    # reference: the plain photo cropped and resized the same way, untouched
    ref = Image.open(plain_path).convert("RGB").crop(box).resize((1500, 1125), Image.LANCZOS)

    # outside the trapezoid: darker and desaturated
    outer = Image.eval(poly_mask(out_trap, 140), lambda v: 255 - v)
    pl, ps = stats(ref, outer)
    ol, os_ = stats(out, outer)
    check(f"{name}: surroundings dimmed to 52-68% ({ol / pl:.2f})", 0.52 <= ol / pl <= 0.68, f"{ol / pl:.2f}")
    check(f"{name}: surroundings desaturated to 40-60% ({os_ / ps:.2f})", 0.40 <= os_ / ps <= 0.60, f"{os_ / ps:.2f}")

    # inside the trapezoid: unchanged apart from the loss of re-saving a WebP
    inner = poly_mask(out_trap, -50)
    buf = io.BytesIO()
    ref.save(buf, "webp", quality=90, method=6)
    resaved = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")
    baseline = ImageStat.Stat(ImageChops.difference(ref, resaved).convert("L"), inner).mean[0]
    diff = ImageStat.Stat(ImageChops.difference(ref, out).convert("L"), inner).mean[0]
    check(f"{name}: trapezoid area unchanged (diff {diff:.2f} within re-save baseline {baseline:.2f} + 0.5)",
          diff <= baseline + 0.5, f"{diff:.2f}")

    # no baked lime outline: no more lime-like pixels than the untouched crop has
    # (streetlit snow in the night photos is naturally close to the lime colour)
    def lime_px(im):
        return sum(1 for p in getattr(im, "get_flattened_data", im.getdata)() if math.dist(p, LIME) < 60)
    near, near_ref = lime_px(out), lime_px(ref)
    check(f"{name}: no lime outline ({near} px, plain crop {near_ref} px)",
          near <= near_ref + 0.0005 * 1500 * 1125, f"{near} px vs {near_ref} px")

# re-running must not compound the effect or change the data
if windrows and emph:
    files = [IMG / f"windrow-{n}{s}.webp" for n in windrows for s in ("", "-750")]
    before = {f: f.read_bytes() if f.exists() else None for f in files}
    subprocess.run([sys.executable, "-I", str(HERE / "emphasize.py")], check=True, stdout=subprocess.DEVNULL)
    after = {f: f.read_bytes() if f.exists() else None for f in files}
    check("re-running gives identical images", before == after, "outputs changed on re-run")
else:
    check("emphasize.py runnable with windrows.json", False, "missing windrows.json or emphasize.py")

print("\nALL PASSED" if not failed else f"\n{failed} FAILED")
sys.exit(1 if failed else 0)
