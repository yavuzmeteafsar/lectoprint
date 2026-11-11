import math
import os
import re
import subprocess
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, Flowable, PageBreak, KeepTogether, CondPageBreak, Image)
from reportlab.lib.utils import ImageReader

def _font_dir():
    for d in ["/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/", "/usr/share/fonts/TTF/",
              "/Library/Fonts/", os.path.expanduser("~/Library/Fonts/")]:
        if os.path.exists(os.path.join(d, "DejaVuSans.ttf")):
            return d
    try:
        p = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans"], capture_output=True, text=True).stdout
        if p.endswith("DejaVuSans.ttf"):
            return os.path.dirname(p) + "/"
    except Exception:
        pass
    raise RuntimeError("DejaVu fonts not found. Install fonts-dejavu (Turkish characters need them).")


FD = _font_dir()
for n, f in [("DV", "DejaVuSans.ttf"), ("DVB", "DejaVuSans-Bold.ttf"), ("DVI", "DejaVuSans-Oblique.ttf"),
             ("DVBI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf"), ("DVMB", "DejaVuSansMono-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n, FD + f))
registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVBI")
registerFontFamily("DVM", normal="DVM", bold="DVMB", italic="DVM", boldItalic="DVMB")
from reportlab.platypus import tables as _tables
_tables.CellStyle.fontname = "DV"

H = colors.HexColor
DEEP = H("#0A4743"); PRIMARY = H("#0F766E"); MID = H("#0D5E58"); CORAL = H("#FF7F50"); CORALD = H("#C2451C")
SAND = H("#F5E6CA"); ABLUE = H("#1565C0"); LBLUE = H("#E3F2FD"); LTEAL = H("#E6F2F0")
NAVY = DEEP; DBLUE = PRIMARY; MBLUE = MID; TEAL = MID; SUMMARY = CORALD
GDARK = H("#1B5E20"); GLIGHT = H("#E8F5E9"); RDARK = H("#B71C1C"); RLIGHT = H("#FFEBEE")
PDARK = H("#4A148C"); PLIGHT = H("#F3E5F5"); YLBG = H("#FFFDE7"); YLBRD = H("#F9A825")
GREY = H("#455A64")

CBG = H("#1E2A35"); CFG = H("#CDD3DE"); CCOM = H("#6A9955"); CKW = H("#569CD6"); CSTR = H("#CE9178")
CFUNC = H("#DCDCAA"); CNUM = H("#B5CEA8"); CTYPE = H("#4EC9B0"); CVAR = H("#9CDCFE"); CPUN = H("#808080")
CALERT = H("#F44747"); CBRD = H("#4A6070"); CLBL = CORAL

PW, PH = A4
LM = RM = 2 * cm
TM = BM = 2.2 * cm
TW = PW - LM - RM

ST = {
    "body": ParagraphStyle("body", fontName="DV", fontSize=10, leading=14.6, spaceAfter=5, textColor=H("#1C1C1C")),
    "bullet": ParagraphStyle("bullet", fontName="DV", bulletFontName="DV", fontSize=10, leading=14.2, leftIndent=14, bulletIndent=3, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="DVB", fontSize=13.5, leading=17, textColor=DBLUE, spaceBefore=10, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="DVB", fontSize=11, leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=9, leading=12),
    "cellb": ParagraphStyle("cellb", fontName="DVB", fontSize=9, leading=12),
    "cellmc": ParagraphStyle("cellmc", fontName="DVM", fontSize=9, leading=12, alignment=TA_CENTER),
    "cellhc": ParagraphStyle("cellhc", fontName="DVB", fontSize=9, leading=12, textColor=colors.white, alignment=TA_CENTER),
    "box": ParagraphStyle("box", fontName="DV", fontSize=9.6, leading=13.6),
    "boxt": ParagraphStyle("boxt", fontName="DVB", fontSize=9.8, leading=13.6),
    "en": ParagraphStyle("en", fontName="DVI", fontSize=9.8, leading=14, textColor=H("#0D2A4F")),
    "q": ParagraphStyle("q", fontName="DVI", fontSize=10, leading=14.5, textColor=H("#2A0E50")),
    "mono": ParagraphStyle("mono", fontName="DVM", fontSize=9.6, leading=13.6, textColor=H("#0B3D3A")),
    "cap": ParagraphStyle("cap", fontName="DVI", fontSize=8.6, leading=11, textColor=GREY, alignment=TA_CENTER),
    "toc": ParagraphStyle("toc", fontName="DV", fontSize=10.5, leading=17),
}

LANGS = {
    "python": dict(kw="False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield",
                   types="int float str list dict set tuple bool bytes object Exception self", com="#"),
    "java": dict(kw="abstract boolean break byte case catch char class continue default do double else enum extends final finally float for if implements import instanceof int interface long new package private protected public return short static super switch this throw throws try void while null true false var",
                 types="String Integer List ArrayList Map HashMap Scanner System Object Connection Statement ResultSet Exception Thread Runnable", com="//"),
    "c": dict(kw="auto break case char const continue default do double else enum extern float for goto if int long register return short signed sizeof static struct switch typedef union unsigned void volatile while NULL",
              types="FILE size_t uint8_t int32_t pid_t", com="//"),
    "sql": dict(kw="SELECT FROM WHERE INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE DROP ALTER ADD JOIN INNER LEFT RIGHT OUTER ON GROUP BY ORDER HAVING AS AND OR NOT NULL PRIMARY KEY FOREIGN REFERENCES DISTINCT LIMIT IN IS LIKE BETWEEN UNION ALL COUNT SUM AVG MIN MAX",
                types="INT INTEGER VARCHAR CHAR TEXT DATE DECIMAL BOOLEAN FLOAT", com="--", ci=True),
    "cpp": dict(kw="alignas auto bool break case catch char class const constexpr continue default delete do double else enum explicit extern false float for friend if inline int long namespace new noexcept nullptr operator private protected public return short signed sizeof static struct switch template this throw true try typedef typename union unsigned using virtual void volatile while include define",
                types="std string vector map set unordered_map pair size_t cout cin endl unique_ptr shared_ptr array deque queue stack", com="//"),
    "javascript": dict(kw="async await break case catch class const continue default delete do else export extends false finally for from function if import in instanceof let new null of return static super switch this throw true try typeof undefined var void while yield",
                       types="Array Object String Number Boolean Promise Map Set JSON Math console document window Error", com="//"),
    "matlab": dict(kw="break case catch classdef continue else elseif end for function global if otherwise parfor persistent return switch try while",
                   types="zeros ones eye size length numel disp fprintf plot figure linspace inv det rank sum max min abs sqrt", com="%"),
    "verilog": dict(kw="module endmodule input output inout wire reg logic assign always always_ff always_comb begin end if else case endcase default posedge negedge parameter localparam integer for initial",
                    types="and or not nand nor xor xnor buf", com="//"),
    "vhdl": dict(kw="ENTITY IS PORT END ARCHITECTURE OF BEGIN SIGNAL PROCESS IF THEN ELSE ELSIF CASE WHEN OTHERS LIBRARY USE ALL IN OUT INOUT CONSTANT TYPE GENERIC MAP COMPONENT AND OR NOT XOR RISING_EDGE",
                 types="STD_LOGIC STD_LOGIC_VECTOR INTEGER BIT BOOLEAN UNSIGNED SIGNED", com="--", ci=True),
    "bash": dict(kw="git cd ls cat echo grep sudo apt pip python3 mkdir rm cp mv chmod export source if then else fi for do done while",
                 types="commit push pull clone checkout branch merge rebase add status log diff init remote fetch stash reset install", com="#"),
}


def _tok_line(line, lang):
    L = LANGS.get(lang)
    out = []
    if L is None:
        return [(line, CFG, False)]
    ci = L.get("ci", False)
    kws = set(L["kw"].split()); tys = set(L["types"].split())
    com = L["com"]
    pat = re.compile(r'(\s+)|("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')|(-{1,2}[A-Za-z][\w-]*)|(\d+(?:\.\d+)?)|(\$?[A-Za-z_]\w*)|(.)')
    i = 0
    while i < len(line):
        if line.startswith(com, i) and (lang != "bash" or i == 0 or line[i - 1] == " "):
            out.append((line[i:], CCOM, False)); break
        if line.startswith("!!", i):
            out.append((line[i + 2:], CALERT, True)); break
        m = pat.match(line, i)
        ws, s, flag, num, word, other = m.groups()
        t = m.group(0)
        if ws:
            out.append((t, CFG, False))
        elif s:
            out.append((t, CSTR, False))
        elif flag and lang == "bash":
            out.append((t, CFUNC, False))
        elif flag:
            out.append((t[0], CPUN, False)); m = re.compile(r"-").match(line, i); t = "-"
        elif num:
            out.append((t, CNUM, False))
        elif word:
            key = t.upper() if ci else t
            nxt = line[m.end():m.end() + 1]
            if key in kws:
                out.append((t, CKW, True))
            elif key in tys:
                out.append((t, CTYPE, True))
            elif nxt == "(":
                out.append((t, CFUNC, False))
            elif lang == "bash" and t.startswith("$"):
                out.append((t, CVAR, False))
            else:
                out.append((t, CVAR if lang != "bash" else CFG, False))
        else:
            out.append((t, CPUN, False))
        i += len(t)
    return out


class CodeBlock(Flowable):
    def __init__(self, code, lang, label=None, fs=8.6):
        super().__init__()
        self.lines = code.split("\n"); self.lang = lang; self.label = label; self.fs = fs
        self.lh = fs * 1.42
    def wrap(self, aw, ah):
        self.aw = aw
        cw = pdfmetrics.stringWidth("M", "DVM", self.fs)
        maxc = int((aw - 20) / cw)
        self.vis = []
        for ln in self.lines:
            ln = ln.replace("\t", "    ")
            while len(ln) > maxc:
                self.vis.append(ln[:maxc]); ln = "  " + ln[maxc:]
            self.vis.append(ln if ln else " ")
        self.h = len(self.vis) * self.lh + 14 + (16 if self.label else 0)
        return aw, self.h
    def split(self, aw, ah):
        self.wrap(aw, ah)
        if self.h <= ah:
            return [self]
        n = max(1, int((ah - 14 - (16 if self.label else 0)) / self.lh))
        if n < 3:
            return []
        a = CodeBlock("\n".join(self.vis[:n]), self.lang, self.label, self.fs)
        b = CodeBlock("\n".join(self.vis[n:]), self.lang, None, self.fs)
        return [a, b]
    def draw(self):
        c = self.canv
        c.setFillColor(CBG); c.setStrokeColor(CBRD); c.setLineWidth(0.8)
        c.roundRect(0, 0, self.aw, self.h, 4, stroke=1, fill=1)
        y = self.h - 8
        if self.label:
            c.setFont("DVMB", 8.6); c.setFillColor(CLBL); c.drawString(10, y - 9, self.label)
            y -= 16
        for ln in self.vis:
            y -= self.lh
            x = 10
            for txt, col, bold in _tok_line(ln, self.lang):
                f = "DVMB" if bold else "DVM"
                c.setFont(f, self.fs); c.setFillColor(col); c.drawString(x, y + 3, txt)
                x += pdfmetrics.stringWidth(txt, f, self.fs)


STR = {
    "en": dict(page="Page %d", toc="Contents", warn="WARNING:", tip="TIP:", orig="SOURCE", orig_tr="SOURCE"),
    "hybrid": dict(page="Sayfa %d", toc="İçindekiler", warn="DİKKAT:", tip="İPUCU:", orig="ORİJİNAL (EN)", tr="TÜRKÇESİ"),
    "tr": dict(page="Sayfa %d", toc="İçindekiler", warn="DİKKAT:", tip="İPUCU:", orig="KAYNAK", orig_tr="KAYNAK (Türkçe çeviri)"),
}


def footer_factory(text, page_fmt="Page %d"):
    def footer(canv, doc):
        canv.saveState()
        if doc.page > 1:
            canv.setStrokeColor(MBLUE); canv.setLineWidth(0.6)
            canv.line(LM, BM - 14, PW - RM, BM - 14)
            canv.setFont("DV", 8); canv.setFillColor(GREY)
            canv.drawString(LM, BM - 26, text)
            canv.drawRightString(PW - RM, BM - 26, page_fmt % doc.page)
        canv.restoreState()
    return footer


class Cover(Flowable):
    def __init__(self, title, sub, lines, bottom):
        super().__init__(); self.title = title; self.sub = sub; self.lines = lines; self.bottom = bottom
    def wrap(self, aw, ah):
        return aw, ah - 2
    def draw(self):
        c = self.canv
        c.saveState(); c.translate(-LM, -BM)
        c.setFillColor(NAVY); c.rect(0, 0, PW, PH, stroke=0, fill=1)
        c.setFillColor(DBLUE); c.rect(0, PH * 0.38, PW, PH * 0.30, stroke=0, fill=1)
        c.setFillColor(CLBL); c.rect(LM, PH * 0.66, 70, 5, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("DVB", 30)
        y = PH * 0.60
        for t in self.title:
            c.drawString(LM, y, t); y -= 38
        c.setFont("DV", 14); c.setFillColor(H("#F5E6CA")); c.drawString(LM, y - 6, self.sub)
        c.setFont("DV", 10.5); c.setFillColor(H("#E9DDC5"))
        y = PH * 0.30
        for l in self.lines:
            c.drawString(LM, y, l); y -= 17
        c.setFont("DVB", 9); c.setFillColor(CLBL); c.drawString(LM, 50, self.bottom)
        c.restoreState()


class SecHdr(Flowable):
    def __init__(self, num, text, bg=NAVY):
        super().__init__(); self.num = num; self.text = text; self.bg = bg
    def wrap(self, aw, ah):
        self.w = aw; return aw, 34
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg); c.roundRect(0, 0, self.w, 30, 4, stroke=0, fill=1)
        c.setFillColor(CLBL); c.roundRect(0, 0, 44, 30, 4, stroke=0, fill=1)
        c.setFillColor(NAVY); c.setFont("DVB", 14); c.drawCentredString(22, 9.5, self.num)
        c.setFillColor(colors.white); c.setFont("DVB", 13.5); c.drawString(56, 10, self.text)


def _ell_pt(cx, cy, rx, ry, dx, dy):
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    t = 1.0 / math.sqrt((ux / rx) ** 2 + (uy / ry) ** 2)
    return cx + ux * t, cy + uy * t


class FA(Flowable):
    def __init__(self, w, h, states, edges, caption=None):
        super().__init__()
        self.dw = w; self.dh = h; self.edges = edges; self.caption = caption
        self.geo = {}
        for name, x, y, fl in states:
            rx = max(15, pdfmetrics.stringWidth(name, "DVB", 9) / 2 + 7)
            self.geo[name] = (x, y, rx, 15, fl)
    def wrap(self, aw, ah):
        self.aw = aw
        return aw, self.dh + (16 if self.caption else 0) + 6
    def _arrow(self, c, x, y, ang, col):
        bx, by = x - 7 * math.cos(ang), y - 7 * math.sin(ang)
        px, py = -math.sin(ang), math.cos(ang)
        p = c.beginPath(); p.moveTo(x, y); p.lineTo(bx + px * 3.4, by + py * 3.4); p.lineTo(bx - px * 3.4, by - py * 3.4); p.close()
        c.setFillColor(col); c.drawPath(p, stroke=0, fill=1)
    def _label(self, c, x, y, text):
        c.setFont("DVB", 8.6)
        tw = pdfmetrics.stringWidth(text, "DVB", 8.6)
        c.setFillColor(colors.white); c.rect(x - tw / 2 - 2, y - 3.5, tw + 4, 11, stroke=0, fill=1)
        c.setFillColor(TEAL); c.drawCentredString(x, y - 0.5, text)
    def draw(self):
        c = self.canv
        ox = (self.aw - self.dw) / 2.0
        oy = 16 if self.caption else 0
        c.saveState()
        c.setFillColor(H("#FBF6EC")); c.setStrokeColor(H("#E8D9BC")); c.setLineWidth(0.6)
        c.roundRect(ox - 8, oy - 2, self.dw + 16, self.dh + 6, 6, stroke=1, fill=1)
        c.translate(ox, oy)
        for e in self.edges:
            col = e.get("col", H("#37474F"))
            c.setStrokeColor(col); c.setLineWidth(1.0)
            sx, sy, srx, sry, _ = self.geo[e["s"]]
            dx_, dy_, drx, dry, _ = self.geo[e["d"]]
            if e["s"] == e["d"]:
                a = math.radians(e.get("ang", 90)); sp = math.radians(24)
                p0 = _ell_pt(sx, sy, srx, sry, math.cos(a - sp), math.sin(a - sp))
                p3 = _ell_pt(sx, sy, srx, sry, math.cos(a + sp), math.sin(a + sp))
                c1 = (p0[0] + math.cos(a - sp * 1.6) * 30, p0[1] + math.sin(a - sp * 1.6) * 30)
                c2 = (p3[0] + math.cos(a + sp * 1.6) * 30, p3[1] + math.sin(a + sp * 1.6) * 30)
                p = c.beginPath(); p.moveTo(*p0); p.curveTo(c1[0], c1[1], c2[0], c2[1], p3[0], p3[1])
                c.drawPath(p, stroke=1, fill=0)
                self._arrow(c, p3[0], p3[1], math.atan2(p3[1] - c2[1], p3[0] - c2[0]), col)
                if abs(math.cos(a)) > 0.7:
                    lx = sx + math.cos(a) * (srx + 26 + pdfmetrics.stringWidth(e["l"], "DVB", 8.6) / 2); ly = sy - 3 + math.sin(a) * 10
                else:
                    lx = sx + math.cos(a) * (srx + 30); ly = sy + math.sin(a) * (sry + 30) - 3
                self._label(c, lx, ly, e["l"])
                continue
            vx, vy = dx_ - sx, dy_ - sy
            n = math.hypot(vx, vy); px, py = -vy / n, vx / n
            bend = e.get("bend", 0)
            mx, my = (sx + dx_) / 2 + px * bend, (sy + dy_) / 2 + py * bend
            p0 = _ell_pt(sx, sy, srx, sry, mx - sx, my - sy)
            p2 = _ell_pt(dx_, dy_, drx, dry, mx - dx_, my - dy_)
            cx_ = 2 * mx - (p0[0] + p2[0]) / 2; cy_ = 2 * my - (p0[1] + p2[1]) / 2
            c1 = (p0[0] + 2.0 / 3 * (cx_ - p0[0]), p0[1] + 2.0 / 3 * (cy_ - p0[1]))
            c2 = (p2[0] + 2.0 / 3 * (cx_ - p2[0]), p2[1] + 2.0 / 3 * (cy_ - p2[1]))
            p = c.beginPath(); p.moveTo(*p0); p.curveTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
            c.drawPath(p, stroke=1, fill=0)
            self._arrow(c, p2[0], p2[1], math.atan2(p2[1] - cy_, p2[0] - cx_), col)
            t = e.get("lp", 0.5)
            qx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx_ + t * t * p2[0]
            qy = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy_ + t * t * p2[1]
            off = e.get("off", 8 if bend >= 0 else -8)
            self._label(c, qx + px * off, qy + py * off - 3, e["l"])
        for name, (x, y, rx, ry, fl) in self.geo.items():
            if "start" in fl:
                a = math.radians(fl.get("sdir", 180) if isinstance(fl, dict) else 180)
                ex, ey = _ell_pt(x, y, rx, ry, math.cos(a), math.sin(a))
                c.setStrokeColor(H("#FF7F50")); c.setLineWidth(1.6)
                c.line(ex + math.cos(a) * 22, ey + math.sin(a) * 22, ex, ey)
                self._arrow(c, ex, ey, a + math.pi, H("#FF7F50"))
            acc = "acc" in fl
            c.setLineWidth(1.3); c.setStrokeColor(NAVY); c.setFillColor(H("#FFD8C7") if acc else H("#EEF6F5"))
            c.ellipse(x - rx, y - ry, x + rx, y + ry, stroke=1, fill=1)
            if acc:
                c.ellipse(x - rx + 3, y - ry + 3, x + rx - 3, y + ry - 3, stroke=1, fill=0)
            c.setFillColor(NAVY); c.setFont("DVB", 9); c.drawCentredString(x, y - 3.2, name)
        c.restoreState()
        if self.caption:
            c.setFont("DVI", 8.6); c.setFillColor(GREY); c.drawCentredString(self.aw / 2, 2, self.caption)


_MATH_DIR = tempfile.mkdtemp(prefix="lectoprint_math_")
_MATH_N = [0]


def render_math(tex, fs=13, color="#0B3D3A"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["mathtext.fontset"] = "dejavusans"
    _MATH_N[0] += 1
    out = os.path.join(_MATH_DIR, "m%04d.png" % _MATH_N[0])
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex if "$" in tex else "$%s$" % tex, fontsize=fs, color=color)
    try:
        fig.savefig(out, dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.04)
    except ValueError as e:
        plt.close(fig)
        raise ValueError("math(): matplotlib mathtext cannot parse %r. It supports a LaTeX subset: "
                         "no \\iff, \\text or matrices; use \\Leftrightarrow, \\mathrm{} and grid(). Details: %s" % (tex, str(e).strip().splitlines()[-1])) from None
    plt.close(fig)
    iw, ih = ImageReader(out).getSize()
    return out, iw * 72.0 / 300, ih * 72.0 / 300


class Doc:
    def __init__(self, path, footer_text, title="Study Notes", author="", lang="en"):
        assert lang in STR, "lang must be en, hybrid or tr"
        self.path = path; self.f = []; self.footer_text = footer_text; self.title = title; self.author = author
        self.lang = lang; self.S = STR[lang]
    def add(self, x): self.f.append(x)
    def cover(self, title_lines, sub, info_lines, bottom):
        self.f.append(Cover(title_lines, sub, info_lines, bottom)); self.f.append(PageBreak())
    def toc(self, entries):
        self.sec_hdr("0", self.S["toc"])
        data = [[Paragraph("<b>%s</b>" % n, ST["toc"]), Paragraph(t, ST["toc"])] for n, t in entries]
        tb = Table(data, colWidths=[TW * 0.1, TW * 0.9])
        tb.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, H("#CFD8DC")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        self.f.append(tb); self.f.append(PageBreak())
    def page_break(self): self.f.append(PageBreak())
    def sec_hdr(self, num, text, bg=NAVY):
        self.f.append(CondPageBreak(7 * cm)); self.f.append(Spacer(1, 6)); self.f.append(SecHdr(num, text, bg)); self.f.append(Spacer(1, 6))
    def h2(self, t):
        self.f.append(CondPageBreak(3.5 * cm)); self.f.append(Paragraph(t, ST["h2"]))
    def h3(self, t):
        self.f.append(CondPageBreak(5 * cm)); self.f.append(Paragraph(t, ST["h3"]))
    def body(self, t): self.f.append(Paragraph(t, ST["body"]))
    def bullets(self, items):
        for i in items:
            self.f.append(Paragraph(i, ST["bullet"], bulletText="•"))
        self.f.append(Spacer(1, 4))
    def sp(self, h=6): self.f.append(Spacer(1, h))
    def _box(self, title, text, bg, brd, tcol, style="box"):
        content = []
        if title:
            content.append(Paragraph('<font color="%s">%s</font>' % ("#" + tcol.hexval()[2:], title), ST["boxt"]))
        for t in ([text] if isinstance(text, str) else text):
            content.append(Paragraph(t, ST[style]))
        tb = Table([[content]], colWidths=[TW])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 4, brd),
                                ("BOX", (0, 0), (-1, -1), 0.5, brd), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        self.f.append(Spacer(1, 3)); self.f.append(tb); self.f.append(Spacer(1, 7))
    def info_box(self, title, text): self._box(title, text, LBLUE, ABLUE, ABLUE)
    def warn_box(self, text, title=None): self._box(title or self.S["warn"], text, RLIGHT, RDARK, RDARK)
    def tip_box(self, text, title=None): self._box(title or self.S["tip"], text, GLIGHT, GDARK, GDARK)
    def hl_box(self, text, title=None): self._box(title, text, YLBG, YLBRD, H("#8D6E00"))
    def q_box(self, label, lines): self._box(label, lines, PLIGHT, PDARK, PDARK, "q")
    def src_box(self, orig, tr=None, src=None):
        orig = [orig] if isinstance(orig, str) else orig
        tr = [tr] if isinstance(tr, str) else tr
        tag = (" &#183; " + src) if src else ""
        if self.lang == "hybrid" and tr:
            rows = [[[Paragraph('<font color="#1565C0"><b>%s</b></font>%s' % (self.S["orig"], tag), ST["boxt"])] + [Paragraph(t, ST["en"]) for t in orig]],
                    [[Paragraph('<font color="#0D5E58"><b>%s</b></font>' % self.S["tr"], ST["boxt"])] + [Paragraph(t, ST["box"]) for t in tr]]]
            bgs = [(LBLUE, ABLUE), (LTEAL, MID)]
        else:
            if self.lang == "tr" and tr:
                label, body = self.S["orig_tr"], tr
            else:
                label, body = self.S["orig"], orig
            rows = [[[Paragraph('<font color="#1565C0"><b>%s</b></font>%s' % (label, tag), ST["boxt"])] + [Paragraph(t, ST["en"]) for t in body]]]
            bgs = [(LBLUE, ABLUE)]
        tb = Table(rows, colWidths=[TW])
        sty = [("BOX", (0, 0), (-1, -1), 0.5, H("#90A4AE")), ("LEFTPADDING", (0, 0), (-1, -1), 10),
               ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
        for k, (bg, brd) in enumerate(bgs):
            sty += [("BACKGROUND", (0, k), (0, k), bg), ("LINEBEFORE", (0, k), (0, k), 4, brd)]
        tb.setStyle(TableStyle(sty))
        self.f.append(Spacer(1, 3)); self.f.append(KeepTogether([tb])); self.f.append(Spacer(1, 7))
    def math(self, lines, fs=13):
        lines = [lines] if isinstance(lines, str) else lines
        cells = []
        for t in lines:
            path, w, h = render_math(t, fs)
            if w > TW - 30:
                h = h * (TW - 30) / w; w = TW - 30
            img = Image(path, width=w, height=h); img.hAlign = "LEFT"
            cells.append(img); cells.append(Spacer(1, 3))
        tb = Table([[cells]], colWidths=[TW])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LTEAL), ("BOX", (0, 0), (-1, -1), 0.6, MID),
                                ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        self.f.append(Spacer(1, 2)); self.f.append(KeepTogether([tb])); self.f.append(Spacer(1, 7))
    def formula(self, lines):
        tb = Table([[[Paragraph(l, ST["mono"]) for l in lines]]], colWidths=[TW])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LTEAL), ("BOX", (0, 0), (-1, -1), 0.6, TEAL),
                                ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        self.f.append(Spacer(1, 2)); self.f.append(tb); self.f.append(Spacer(1, 7))
    def def_tbl(self, rows, w0=0.27):
        data = [[Paragraph(a, ST["cellb"]), Paragraph(b, ST["cell"])] for a, b in rows]
        tb = Table(data, colWidths=[TW * w0, TW * (1 - w0)])
        sty = [("GRID", (0, 0), (-1, -1), 0.4, H("#B0BEC5")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
               ("BACKGROUND", (0, 0), (0, -1), LBLUE), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
        sty += [("BACKGROUND", (1, i), (1, i), H("#F7F9FC")) for i in range(1, len(rows), 2)]
        tb.setStyle(TableStyle(sty))
        self.f.append(tb); self.f.append(Spacer(1, 8))
    def grid(self, header, rows, widths=None, mono_cols=None, hl_rows=(), red_rows=(), green_rows=(), caption=None):
        mono_cols = list(range(len(header))) if mono_cols is None else mono_cols
        data = [[Paragraph(h, ST["cellhc"]) for h in header]]
        data += [[Paragraph(str(v), ST["cellmc"] if j in mono_cols else ST["cell"]) for j, v in enumerate(r)] for r in rows]
        widths = [TW / len(header)] * len(header) if widths is None else [TW * w / sum(widths) for w in widths]
        tb = Table(data, colWidths=widths, repeatRows=1)
        sty = [("BACKGROUND", (0, 0), (-1, 0), DBLUE), ("GRID", (0, 0), (-1, -1), 0.4, H("#B0BEC5")),
               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5)]
        sty += [("BACKGROUND", (0, i), (-1, i), H("#F5F7FB")) for i in range(2, len(data), 2)]
        sty += [("BACKGROUND", (0, i + 1), (-1, i + 1), YLBG) for i in hl_rows]
        sty += [("BACKGROUND", (0, i + 1), (-1, i + 1), RLIGHT) for i in red_rows]
        sty += [("BACKGROUND", (0, i + 1), (-1, i + 1), GLIGHT) for i in green_rows]
        tb.setStyle(TableStyle(sty))
        items = [tb] + ([Spacer(1, 2), Paragraph(caption, ST["cap"])] if caption else [])
        self.f.append(KeepTogether(items)); self.f.append(Spacer(1, 8))
    def code_block_hl(self, code, lang="python", label=None):
        self.f.append(Spacer(1, 3)); self.f.append(CodeBlock(code.strip("\n"), lang, label)); self.f.append(Spacer(1, 8))
    def diagram(self, w, h, states, edges, caption=None):
        self.f.append(Spacer(1, 2)); self.f.append(FA(w, h, states, edges, caption)); self.f.append(Spacer(1, 8))
    def image(self, path, width_frac=0.75, caption=None):
        iw, ih = ImageReader(path).getSize()
        w = TW * width_frac; h = w * ih / iw
        maxh = PH - TM - BM - 60
        if h > maxh:
            h = maxh; w = h * iw / ih
        img = Image(path, width=w, height=h)
        img.hAlign = "CENTER"
        items = [img] + ([Spacer(1, 3), Paragraph(caption, ST["cap"])] if caption else [])
        self.f.append(Spacer(1, 4)); self.f.append(KeepTogether(items)); self.f.append(Spacer(1, 8))
    def build(self):
        d = BaseDocTemplate(self.path, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                            title=self.title, author=self.author, initialFontName="DV", initialFontSize=10)
        fr = Frame(LM, BM, TW, PH - TM - BM, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        d.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=footer_factory(self.footer_text, self.S["page"]))])
        d.build(self.f)
