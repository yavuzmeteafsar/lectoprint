import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ASCII_TR = ["Donusum", "donusum", "Adim", "adim", "icin", "cunku", "Sinav", "sinav", "Ozet", "ozet", "Tanim", "tanim", "Dogru", "Yanlis", "degil"]
EN_WORDS = ["the", "and", "which", "state", "states", "string", "answer", "true", "false", "subset", "closure"]
LM = RM = 56.69
TM = BM = 62.36
EDGE_TOL = 3.0
INK = 245
ASCII_MATH = re.compile(r"[\u03b1-\u03c9\u0391-\u03a9]_[A-Za-z0-9]|[A-Za-z0-9)\]]\^[\w(\-\u2212]")
RAW_MARKUP = re.compile(r"</?(?:b|i|u|sub|super|sup|font|br|para|strike)\b[^>]*>|&(?:amp|lt|gt|quot|nbsp|#\d+);")


def run(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout


def page_count(path):
    return int(re.search(r"Pages:\s+(\d+)", run("pdfinfo", path)).group(1))


def ranges(pages):
    out, run_ = [], []
    for p in sorted(set(pages)):
        if run_ and p == run_[-1] + 1:
            run_.append(p)
            continue
        if run_:
            out.append("%d-%d" % (run_[0], run_[-1]) if len(run_) > 1 else str(run_[0]))
        run_ = [p]
    if run_:
        out.append("%d-%d" % (run_[0], run_[-1]) if len(run_) > 1 else str(run_[0]))
    return ", ".join(out)


def font_and_language(path, lang):
    errors = []
    for line in run("pdffonts", path).splitlines()[2:]:
        cols = line.split()
        name = cols[0]
        if "DejaVu" not in name and not name.startswith("["):
            errors.append("non-DejaVu font: %s" % name)
        if "no" in cols[-5:-3]:
            errors.append("font not embedded: %s" % name)
    text = run("pdftotext", "-layout", path, "-")
    if not text.strip():
        errors.append("no text extracted")
    if lang in ("hybrid", "tr"):
        for w in ASCII_TR:
            if re.search(r"\b%s\b" % w, text):
                errors.append("ASCII-flattened Turkish word: %s" % w)
    if lang == "tr":
        body = re.sub(r"\([^)]*\)", " ", text)
        for w in EN_WORDS:
            if re.search(r"\b%s\b" % w, body, re.IGNORECASE):
                errors.append("English word outside parentheses in tr mode: %s" % w)
    return errors


def raw_markup(path, pattern=RAW_MARKUP):
    found = {}
    for n, page in enumerate(run("pdftotext", path, "-").split("\f"), 1):
        for m in pattern.findall(page):
            found.setdefault(m, set()).add(n)
    return found


def layout(path, pages):
    from PIL import Image

    blank, overflow = [], []
    with tempfile.TemporaryDirectory() as tmp:
        run("pdftoppm", "-gray", "-r", "72", path, os.path.join(tmp, "p"))
        files = sorted(os.listdir(tmp), key=lambda f: int(re.findall(r"\d+", f)[-1]))
        for n, f in enumerate(files, 1):
            if n == 1:
                continue
            im = Image.open(os.path.join(tmp, f)).convert("L")
            w, h = im.size
            frame = im.crop((int(LM), int(TM), int(w - RM), int(h - BM)))
            if frame.getextrema()[0] >= INK:
                blank.append(n)
            strips = [im.crop((0, 0, int(LM - EDGE_TOL), h)), im.crop((int(w - RM + EDGE_TOL), 0, w, h)),
                      im.crop((0, 0, w, int(TM - EDGE_TOL)))]
            if any(s.getextrema()[0] < INK for s in strips):
                overflow.append(n)
    return blank, overflow


def figures(path, figures_json):
    data = json.load(open(figures_json, encoding="utf-8"))
    crops = [f for f in data["figures"] if not f.get("duplicate_of")]
    sizes = {}
    for line in run("pdfimages", "-list", path).splitlines()[2:]:
        cols = line.split()
        if len(cols) > 4 and cols[2] == "image":
            sizes[(int(cols[3]), int(cols[4]))] = sizes.get((int(cols[3]), int(cols[4])), 0) + 1
    found, missing = [], []
    for f in crops:
        from PIL import Image
        img = Image.open(os.path.join(os.path.dirname(figures_json), f["file"]))
        (found if img.size in sizes else missing).append(f["file"])
    return found, missing


def check(path, lang, figures_json=None):
    pages = page_count(path)
    errors = font_and_language(path, lang)
    blank, overflow = layout(path, pages)
    errors += ["empty page: %s" % ranges(blank)] if blank else []
    errors += ["content past the margins: page %s" % ranges(overflow)] if overflow else []
    notes = []
    raw = raw_markup(path)
    for tag, where in sorted(raw.items()):
        notes.append("markup printed as text: %s on page %s. sec_hdr, cover, diagram and code labels take plain text; "
                     "unless it is real content such as HTML code, rewrite that text without tags" % (tag, ranges(where)))
    stand_ins = raw_markup(path, ASCII_MATH)
    if stand_ins:
        pages_ = sorted(set().union(*stand_ins.values()))
        notes.append("ASCII sub/superscript written out: %s on page %s. Outside sec_hdr, cover and diagrams use "
                     "<sub>/<super> (e.g. \u03c9<sub>n</sub>, e<super>st</super>); in sec_hdr word it without them; "
                     "ignore if it is real code (MATLAB x^2)" % (", ".join(sorted(stand_ins)), ranges(pages_)))
    marks = {}
    side = os.path.splitext(path)[0] + ".layout.json"
    if os.path.exists(side):
        marks = json.load(open(side, encoding="utf-8"))
    look = {}
    for p in marks.get("diagram", []):
        look.setdefault(p, []).append("diagram")
    for p in marks.get("image", []):
        look.setdefault(p, []).append("figure")
    for p in marks.get("table", []):
        look.setdefault(p, []).append("table")
    for p in blank:
        look.setdefault(p, []).append("empty")
    for p in overflow:
        look.setdefault(p, []).append("overflow")
    for p in sorted(set().union(*raw.values()) if raw else []):
        look.setdefault(p, []).append("markup")
    for p in sorted(set().union(*stand_ins.values()) if stand_ins else []):
        look.setdefault(p, []).append("ascii-math")
    if figures_json:
        found, missing = figures(path, figures_json)
        notes.append("figures: %d image() figures in the PDF; %d of %d crops from figures.json used"
                     % (len(marks.get("image", [])), len(found), len(found) + len(missing)))
        if missing:
            notes.append("crops not in the PDF (confirm each was dropped, redrawn or replaced on purpose): "
                         + ", ".join(missing))
    return pages, errors, notes, look


def preview(path, look, out_dir, dpi):
    os.makedirs(out_dir, exist_ok=True)
    files = []
    for p in sorted(look):
        base = os.path.join(out_dir, "p%03d" % p)
        run("pdftoppm", "-png", "-r", str(dpi), "-f", str(p), "-l", str(p), "-singlefile", path, base)
        files.append(base + ".png")
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a Lectoprint PDF: fonts, language, empty pages, margins, figures.")
    ap.add_argument("pdfs", nargs="+", help="out.pdf:lang (lang is en, hybrid or tr)")
    ap.add_argument("--figures", help="figures.json written by find_figures.py")
    ap.add_argument("--preview", help="folder for PNGs of the pages to look at")
    ap.add_argument("--dpi", type=int, default=100)
    args = ap.parse_args(argv)
    failed = False
    for arg in args.pdfs:
        path, lang = arg.rsplit(":", 1)
        pages, errors, notes, look = check(path, lang, args.figures)
        print("%s [%s] %d pages: %s" % (path, lang, pages, "OK" if not errors else "FAIL"))
        for e in errors:
            print("   - " + e)
        for n in notes:
            print("   * " + n)
        if look:
            print("   look at: " + "; ".join("p%d %s" % (p, "+".join(r)) for p, r in sorted(look.items())))
        else:
            print("   look at: nothing flagged")
        if args.preview and look:
            out = args.preview if len(args.pdfs) == 1 else os.path.join(args.preview, os.path.splitext(os.path.basename(path))[0])
            preview(path, look, out, args.dpi)
            print("   previews: %s" % out)
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
