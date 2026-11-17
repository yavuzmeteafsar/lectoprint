import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CHARS_PER_TOKEN = 4.0
MAX_EDGE = 1568
MAX_PIXELS = 1.15e6
ASSUMPTIONS = """Estimated tokens Claude spends on one deck, per skill version.
Text: characters / 4. Images: width * height / 750 after Claude's resize (long edge <= 1568 px, <= 1.15 MP).
Versions: base = before A; A = find_figures; f1 = A + phase 1 rules; f2 = f1 + extract/check_pdf.
- SKILL.md is read once in every version.
- doc_builder.py is read once in base and A, not at all in f1 and f2.
- Source: base, A and f1 read the PDF text and view every page at 100 dpi; f2 reads source.txt and views
  only the pages extract.py marks as little text at 100 dpi (figure pages are seen through their crops).
- Figures: base views each figure page at 50 dpi to locate the figure, then each crop at 200 dpi; A, f1 and f2
  read the find_figures output and view the non-duplicate crops on sheets of six (3 x 2 cells of 500 x 300 px).
- Output preview (the repo's three example PDFs): base, A and f1 view all pages on sheets of six at 60 dpi and
  diagram pages again at 110 dpi; f2 views only the pages check_pdf flags, at 100 dpi.
- One fix: base and A rewrite build.py (output tokens = its size); f1 and f2 make one targeted edit (~150).
- Writing: with --output-pdf, the build files Claude writes are taken as 1.3 x the text of that finished PDF
  (markup and calls around the text); the same in every version.
Not counted: every tool call re-sends the whole conversation so far, so images and long reads early in a run are
paid again on each later turn. This is why real usage falls less than these totals."""


def tok_text(chars):
    return int(math.ceil(chars / CHARS_PER_TOKEN))


def tok_image(w, h):
    s = min(1.0, MAX_EDGE / max(w, h), math.sqrt(MAX_PIXELS / (w * h)))
    return int(round(w * s) * round(h * s) / 750)


def page_size(pdf, page=1):
    out = subprocess.run(["pdfinfo", "-f", str(page), "-l", str(page), str(pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Page\s+%d size:\s+([\d.]+) x ([\d.]+)" % page, out) or re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out)
    return float(m.group(1)), float(m.group(2))


def page_view(pdf, dpi):
    w, h = page_size(pdf)
    return tok_image(w * dpi / 72, h * dpi / 72)


def git_show(rev, path):
    return subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (rev, path)], capture_output=True, text=True,
                          check=True).stdout


def sheet_tokens(n_items, per_sheet=6, cell=(500, 300), cols=3):
    full, rest = divmod(n_items, per_sheet)
    t = full * tok_image(cols * cell[0], (per_sheet // cols) * cell[1])
    if rest:
        rows = math.ceil(rest / cols)
        t += tok_image(min(rest, cols) * cell[0], rows * cell[1])
    return t


def source_costs(pdf, scripts, tmp):
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    figs = Path(tmp) / "figs"
    ff = subprocess.run([sys.executable, str(scripts / "find_figures.py"), str(pdf), str(figs)], capture_output=True,
                        text=True, check=True).stdout
    fj = json.loads((figs / "figures.json").read_text())
    crops = fj["figures"]
    uniq = [c for c in crops if not c.get("duplicate_of")]
    ex = subprocess.run([sys.executable, str(scripts / "extract.py"), str(pdf), str(Path(tmp) / "src"), "--figures",
                         str(figs / "figures.json"), "--no-render"], capture_output=True, text=True, check=True).stdout
    pj = json.loads((Path(tmp) / "src" / "pages.json").read_text())
    src_chars = len((Path(tmp) / "src" / "source.txt").read_text(encoding="utf-8"))
    crop_tok = sum(tok_image(c["box_px"]["W"], c["box_px"]["H"]) for c in crops)
    return {
        "pages": pages,
        "text": tok_text(src_chars),
        "all_pages": pages * page_view(pdf, 100),
        "look_pages": len(pj["little_text"]) * page_view(pdf, 100),
        "n_look": len(pj["little_text"]),
        "fig_locate": len(fj["figure_pages"]) * page_view(pdf, 50) + crop_tok,
        "fig_script": tok_text(len(ff)) + tok_text(len(ex)) + sheet_tokens(len(uniq)),
        "n_crops": len(crops),
        "n_uniq": len(uniq),
    }


def preview_costs(scripts, tmp):
    base = new = 0
    for b in ("build_en_full", "build_hybrid_quick", "build_tr_questions"):
        pdf = Path(tmp) / (b + ".pdf")
        env = dict(os.environ, PYTHONPATH=str(scripts))
        subprocess.run([sys.executable, str(ROOT / "examples" / "src" / (b + ".py")), str(pdf)], check=True,
                       capture_output=True, env=env)
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
        lay = json.loads(pdf.with_suffix(".layout.json").read_text())
        diagrams = len(lay["diagram"])
        w, h = page_size(pdf)
        sheet = tok_image(3 * w * 60 / 72, 2 * h * 60 / 72)
        base += math.ceil(n / 6) * sheet + diagrams * page_view(pdf, 110)
        out = subprocess.run([sys.executable, str(scripts / "check_pdf.py"), "%s:en" % pdf], capture_output=True, text=True).stdout
        flagged = len(re.findall(r"p\d+ [a-z+]+", out.split("look at:")[-1])) if "look at:" in out else 0
        new += flagged * page_view(pdf, 100) + tok_text(len(out))
    return base, new


def main():
    ap = argparse.ArgumentParser(description=ASSUMPTIONS, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+", type=Path)
    ap.add_argument("--revs", default="01712ea,dbb3bdc,d9e3569,27e6167", help="base,A,f1,f2 commits")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--output-pdf", type=Path, help="a finished study PDF from this deck, to estimate the writing")
    args = ap.parse_args()
    revs = dict(zip(["base", "A", "f1", "f2"], args.revs.split(",")))
    skill = {k: tok_text(len(git_show(r, "lectoprint/SKILL.md"))) for k, r in revs.items()}
    builder = tok_text(len(git_show(revs["base"], "lectoprint/scripts/doc_builder.py")))
    rewrite = tok_text(len(git_show(revs["base"], "examples/src/build_en_full.py")))
    scripts = ROOT / "lectoprint" / "scripts"
    write = 0
    if args.output_pdf:
        out_text = subprocess.run(["pdftotext", str(args.output_pdf), "-"], capture_output=True, text=True, check=True).stdout
        write = tok_text(1.3 * len(out_text))
    with tempfile.TemporaryDirectory() as tmp:
        prev_base, prev_new = preview_costs(scripts, tmp)
        rows = {}
        for pdf in args.pdfs:
            with tempfile.TemporaryDirectory() as t2:
                s = source_costs(pdf, scripts, t2)
            r = {}
            for v in ("base", "A", "f1", "f2"):
                c = {"skill": skill[v], "builder": builder if v in ("base", "A") else 0}
                c["source"] = s["text"] + (s["look_pages"] if v == "f2" else s["all_pages"])
                c["figures"] = s["fig_locate"] if v == "base" else s["fig_script"]
                c["preview"] = prev_new if v == "f2" else prev_base
                c["fix"] = rewrite if v in ("base", "A") else 150
                c["write"] = write
                c["total"] = sum(c.values())
                r[v] = c
            r["info"] = s
            rows[pdf.name] = r
    print(ASSUMPTIONS)
    for name, r in rows.items():
        i = r["info"]
        print("\n%s: %d pages, %d figure crops (%d unique), %d little-text pages" % (name, i["pages"], i["n_crops"], i["n_uniq"], i["n_look"]))
        print("%-9s %8s %8s %8s %8s" % ("", "base", "A", "f1", "f2"))
        for k in ("skill", "builder", "source", "figures", "preview", "fix", "write", "total"):
            print("%-9s %8d %8d %8d %8d" % (k, r["base"][k], r["A"][k], r["f1"][k], r["f2"][k]))
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
