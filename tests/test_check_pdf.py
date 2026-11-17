import json
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.platypus import Table

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lectoprint" / "scripts"))
import check_pdf
import doc_builder as db


def crop(path, size, colour):
    im = Image.new("RGB", size, "white")
    ImageDraw.Draw(im).rectangle([10, 10, size[0] - 10, size[1] - 10], outline=colour, width=6)
    im.save(path)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        figs = os.path.join(tmp, "figs")
        os.makedirs(figs)
        crop(os.path.join(figs, "p003_f1.png"), (640, 400), "blue")
        crop(os.path.join(figs, "p007_f1.png"), (500, 300), "red")
        json.dump({"figures": [{"file": "p003_f1.png", "duplicate_of": None},
                               {"file": "p007_f1.png", "duplicate_of": None},
                               {"file": "p009_f1.png", "duplicate_of": "p003_f1.png"}]},
                  open(os.path.join(figs, "figures.json"), "w"))
        out = os.path.join(tmp, "out.pdf")
        d = db.Doc(out, "Test", "Test", "", lang="en")
        d.cover(["Test"], "check_pdf", ["-"], "LECTOPRINT")
        d.sec_hdr("1", "Figures and A<super>st</super>")
        d.image(os.path.join(figs, "p003_f1.png"), caption="Source: p.3")
        d.page_break()
        d.page_break()
        d.body("After an empty page.")
        d.add(Table([["x" * 40, "y" * 40, "z" * 40]], colWidths=[260, 260, 260]))
        d.grid(["Term", "Definition", "Kaynak"], [["Time constant", "tau = RC", "s12"]], widths=[1.6, 4.6, 0.6], mono_cols=[2])
        d.diagram(300, 120, [("q0", 60, 60, ("start",)), ("q1", 220, 60, ("acc",))], [dict(s="q0", d="q1", l="a")])
        d.build()
        pages, errors, notes, look = check_pdf.check(out, "en", os.path.join(figs, "figures.json"))
        print(pages, errors, notes, look)
        assert any(e.startswith("empty page: 3") for e in errors), errors
        assert any(e.startswith("content past the margins: page 4") for e in errors), errors
        assert look.get(2)[0] == "figure", look
        assert "diagram" in look.get(4, []) and "overflow" in look.get(4, []) and "table" in look.get(4, []), look
        d2 = db.Doc(os.path.join(tmp, "ok.pdf"), "Test", "Test", "", lang="hybrid")
        d2.grid(["Term", "Definition (kaynaktaki İngilizce)", "Kaynak"], [["Time constant", "tau = RC", "s10–11"]],
                widths=[1.6, 4.4, 0.8], mono_cols=[2])
        d2.build()
        assert json.load(open(os.path.join(tmp, "ok.layout.json")))["table"] == [], "glossary widths flagged"
        assert "1 of 2 crops from figures.json used" in notes[2], notes
        assert notes[3].endswith("p007_f1.png"), notes
        assert notes[0].startswith("markup printed as text: </super> on page 2"), notes
        assert notes[1].startswith("markup printed as text: <super> on page 2"), notes
        assert "markup" in look.get(2, []), look
        prev = check_pdf.preview(out, look, os.path.join(tmp, "prev"), 60)
        assert len(prev) == len(look) and all(os.path.exists(p) for p in prev)
        print("check_pdf: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
