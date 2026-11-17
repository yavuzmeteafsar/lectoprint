import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


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
    return ", ".join(out) or "none"


def page_texts(pdf):
    out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return [re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", p)).strip() for p in pages]


def figure_pages(pdf, figures_json):
    if figures_json:
        return set(json.load(open(figures_json, encoding="utf-8"))["figure_pages"]), None
    sys.path.insert(0, str(HERE))
    try:
        import find_figures
        return set(find_figures.page_pictures(Path(pdf))), None
    except ImportError:
        return set(), "pypdfium2 is missing, figure pages not marked: pip install pypdfium2"
    except Exception as exc:
        return set(), "figure pages not marked: %s" % exc


def visual_pages(pdf, min_share=0.025, min_paths=8):
    try:
        import pypdfium2 as pdfium
        import pypdfium2.raw as raw
    except ImportError:
        return None
    out = set()
    doc = pdfium.PdfDocument(str(pdf))
    try:
        for i in range(len(doc)):
            page = doc[i]
            size = page.get_width() * page.get_height()
            paths = 0
            for o in page.get_objects(max_depth=4):
                if o.type == raw.FPDF_PAGEOBJ_IMAGE:
                    try:
                        l, b, r, t = o.get_bounds()
                    except Exception:
                        continue
                    if (r - l) * (t - b) >= min_share * size:
                        out.add(i + 1)
                        break
                elif o.type == raw.FPDF_PAGEOBJ_PATH:
                    paths += 1
            if paths >= min_paths:
                out.add(i + 1)
            page.close()
    finally:
        doc.close()
    return out


def extract(pdf, out_dir, min_chars=200, figures_json=None, dpi=100, render=True, all_little=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    texts = page_texts(pdf)
    figs, warning = figure_pages(pdf, figures_json)
    visual = None if all_little else visual_pages(pdf)
    pages = []
    with open(out_dir / "source.txt", "w", encoding="utf-8") as fh:
        for n, t in enumerate(texts, 1):
            chars = len(re.sub(r"\s", "", t))
            little = chars < min_chars and (visual is None or n in visual)
            reasons = (["little text"] if little else []) + (["figure"] if n in figs else [])
            pages.append({"page": n, "chars": chars, "look": bool(reasons), "reasons": reasons})
            fh.write("=== Page %d ===\n%s\n\n" % (n, t))
    little = [p["page"] for p in pages if "little text" in p["reasons"]]
    if render and little:
        look_dir = out_dir / "look"
        look_dir.mkdir(exist_ok=True)
        for n in little:
            subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(n), "-l", str(n), "-singlefile", str(pdf),
                            str(look_dir / ("p%03d" % n))], check=True)
    summary = {"source": str(pdf), "pages": len(pages), "min_chars": min_chars,
               "little_text": little, "figure_pages": sorted(figs), "page_info": pages}
    (out_dir / "pages.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary, warning


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract a source PDF's text and mark the pages to look at as images.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--min-chars", type=int, default=200, help="a page with fewer characters is looked at as an image")
    ap.add_argument("--figures", help="figures.json from find_figures.py (otherwise figure pages are found here)")
    ap.add_argument("--dpi", type=int, default=100)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--all-little", action="store_true",
                    help="mark every page under --min-chars, also those with nothing but text on them")
    args = ap.parse_args(argv)
    try:
        s, warning = extract(args.pdf, args.out_dir, args.min_chars, args.figures, args.dpi, not args.no_render, args.all_little)
    except Exception as exc:
        print("Could not read %s: %s" % (args.pdf, exc), file=sys.stderr)
        return 1
    chars = sum(p["chars"] for p in s["page_info"])
    print("%d pages, %d characters of text -> %s" % (s["pages"], chars, args.out_dir / "source.txt"))
    print("little text (look at %s): %s" % ("look/pNNN.png" if not args.no_render else "the page", ranges(s["little_text"])))
    print("figures (look at the find_figures crops): %s" % ranges(s["figure_pages"]))
    if warning:
        print(warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
