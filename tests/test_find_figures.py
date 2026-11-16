import json
import os
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lectoprint" / "scripts"))
import find_figures

W, H = 960, 540
EXPECTED = {2: {"drawing"}, 5: {"image"}, 7: {"drawing", "image"}, 8: {"image"}}


def png(path, kind):
    fig, ax = plt.subplots(figsize=(4, 2.6), dpi=100)
    if kind == "logo":
        fig.set_size_inches(1, 1)
        ax.add_patch(plt.Circle((0.5, 0.5), 0.4, color="#0F766E"))
        ax.set_axis_off()
    else:
        xs = [i / 10 for i in range(60)]
        ax.plot(xs, [x * x % 7 for x in xs])
        ax.set_xlabel("t (s)")
    fig.savefig(path)
    plt.close(fig)


def header(c, logo, title):
    c.drawImage(logo, W - 60, H - 60, 40, 40)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(40, H - 60, title)
    c.setFont("Helvetica", 16)


def circuit(c, x0, y0):
    c.setLineWidth(1.5)
    for a, b, cc, d in [(0, 0, 100, 0), (140, 0, 260, 0), (0, 0, 0, 160), (260, 0, 260, 62), (260, 98, 260, 160),
                        (0, 160, 30, 160), (248, 160, 260, 160), (100, 0, 100, 40), (140, 0, 140, 48)]:
        c.line(x0 + a, y0 + b, x0 + cc, y0 + d)
    for i in range(6):
        x = x0 + 30 + i * 38
        c.line(x, y0 + 160, x + 10, y0 + 172)
        c.line(x + 10, y0 + 172, x + 20, y0 + 148)
        c.line(x + 20, y0 + 148, x + 28, y0 + 160)
    c.line(x0 + 85, y0 + 40, x0 + 115, y0 + 40)
    c.line(x0 + 125, y0 + 48, x0 + 155, y0 + 48)
    c.circle(x0 + 260, y0 + 80, 18)
    c.setFont("Helvetica", 11)
    c.drawString(x0 + 100, y0 + 182, "R1 = 4.7k")
    c.drawString(x0 + 140, y0 + 20, "Vs")
    c.setFont("Helvetica", 16)


def bullets(c, x, y, lines):
    for i, t in enumerate(lines):
        c.drawString(x, y - i * 26, "• " + t)


def build(pdf, tmp):
    logo, plot = os.path.join(tmp, "logo.png"), os.path.join(tmp, "plot.png")
    png(logo, "logo")
    png(plot, "plot")
    c = canvas.Canvas(pdf, pagesize=(W, H))
    header(c, logo, "Week 3: RC Circuits")
    c.drawString(40, 300, "EEE 201 - Fall 2026")
    c.showPage()
    header(c, logo, "Series RC circuit")
    bullets(c, 40, 420, ["Capacitor charges", "tau = RC", "Voltage rises"])
    circuit(c, 560, 180)
    c.showPage()
    header(c, logo, "Component values")
    t = Table([["Part", "Value", "Unit"], ["R1", "4.7", "kOhm"], ["C1", "10", "uF"], ["Vs", "5", "V"],
               ["tau", "47", "ms"]], colWidths=[140, 140, 140], rowHeights=36)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, "black"), ("FONTSIZE", (0, 0), (-1, -1), 14)]))
    t.wrapOn(c, W, H)
    t.drawOn(c, 270, 160)
    c.showPage()
    header(c, logo, "Course page")
    bullets(c, 40, 420, ["Scan for the lab sheet"])
    for i in range(21):
        for j in range(21):
            if (i * 7 + j * 3) % 5 < 2:
                c.rect(700 + i * 6, 200 + j * 6, 6, 6, stroke=0, fill=1)
    c.showPage()
    header(c, logo, "Charging curve")
    c.drawImage(plot, 230, 60, 500, 325)
    c.showPage()
    header(c, logo, "Summary")
    bullets(c, 40, 420, ["tau = RC sets the speed", "After 5 tau the capacitor is full",
                         "The current falls as the voltage rises"])
    c.setLineWidth(1)
    c.rect(30, 300, 600, 150)
    c.showPage()
    header(c, logo, "Circuit and its response")
    circuit(c, 40, 140)
    c.drawImage(plot, 520, 120, 400, 260)
    c.showPage()
    header(c, logo, "Charging curve again")
    c.drawImage(plot, 230, 60, 500, 325)
    c.showPage()
    header(c, logo, "Next step (hidden until clicked)")
    c.drawImage(plot, 230, 60, 500, 325)
    c.setFillColorRGB(1, 1, 1)
    c.rect(220, 50, 520, 345, stroke=0, fill=1)
    c.showPage()
    c.save()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "deck.pdf")
        build(pdf, tmp)
        out = Path(tmp) / "figs"
        summary = find_figures.find_figures(Path(pdf), out)
        got = {}
        for f in summary["figures"]:
            got.setdefault(f["page"], set()).add(f["kind"])
            assert (out / f["file"]).is_file(), f["file"]
        assert json.loads((out / "figures.json").read_text())["figures"] == summary["figures"]
        dups = {f["file"]: f["duplicate_of"] for f in summary["figures"] if f["duplicate_of"]}
        assert dups == {"p008_f1.png": "p005_f1.png"}, dups
        for f in summary["figures"]:
            print("p%d f%d %s %s" % (f["page"], f["index"], f["kind"], f["box_px"]))
        if got != EXPECTED:
            print("expected %s, got %s" % (EXPECTED, got))
            return 1
        print("find_figures: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
