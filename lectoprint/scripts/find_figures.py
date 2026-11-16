# Adapted from IEUStudia (https://github.com/mirzaisi/IEUStudia), MIT License,
# Copyright (c) 2026 IEUStudia contributors. Source: src/studia/outputs/figures.py
# at commit 23d7bd1 (IEUStudia 4.1.2). Full license text: lectoprint/THIRD_PARTY_NOTICES.md.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Box = Tuple[float, float, float, float]
MIN_SHARE = 0.025
MAX_SHARE = 0.9
CROP_MAX = 0.7
DRAW_MIN, DRAW_MAX = 0.03, 0.6
DRAW_PATHS = 8
GAP = 7.0
MARGIN = 12.0
LINE_MAX = 2.5
FIGURE_GAP = 30.0


def _area(b: Box) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _union(boxes: List[Box]) -> Box:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _near(a: Box, b: Box, gap: float) -> bool:
    return a[0] - gap <= b[2] and b[0] - gap <= a[2] and a[1] - gap <= b[3] and b[1] - gap <= a[3]


def _clusters(boxes: List[Box], gap: float) -> List[List[Box]]:
    groups: List[List[Box]] = []
    for b in sorted(boxes):
        joined = [g for g in groups if any(_near(b, x, gap) for x in g)]
        merged = [b] + [x for g in joined for x in g]
        groups = [g for g in groups if not any(g is j for j in joined)] + [merged]
    return groups


def _words(textpage: Any, box: Box) -> int:
    try:
        return len(textpage.get_text_bounded(*box).split())
    except Exception:
        return 0


def _text_runs(textpage: Any) -> List[Box]:
    try:
        return [textpage.get_rect(i) for i in range(textpage.count_rects())]
    except Exception:
        return []


def _running_text(runs: List[Box], box: Box) -> bool:
    width = box[2] - box[0]
    inside = [r for r in runs if r[0] >= box[0] - 2 and r[2] <= box[2] + 2 and r[1] >= box[1] - 2 and r[3] <= box[3] + 2]
    return sum(1 for r in inside if r[2] - r[0] > 0.5 * width) >= 2


def _page_pictures(page: Any, textpage: Any) -> List[Tuple[str, Box]]:
    import pypdfium2.raw as raw

    w, h = page.get_width(), page.get_height()
    size = w * h
    images: List[Box] = []
    paths: List[Box] = []
    for o in page.get_objects(max_depth=4):
        if o.type not in (raw.FPDF_PAGEOBJ_IMAGE, raw.FPDF_PAGEOBJ_PATH):
            continue
        try:
            l, b, r, t = o.get_bounds()
        except Exception:
            continue
        box = (max(0.0, l), max(0.0, b), min(w, r), min(h, t))
        share = _area(box) / size
        if o.type == raw.FPDF_PAGEOBJ_IMAGE:
            if MIN_SHARE <= share <= MAX_SHARE:
                images.append(box)
            continue
        bw, bh = box[2] - box[0], box[3] - box[1]
        if share > 0.06 or (min(bw, bh) < 2.5 and max(bw / w, bh / h) > 0.5):
            continue
        if bw < 0.02 * w and bh < 0.02 * h and abs(bw - bh) < 1.0:
            continue
        paths.append(box)
    out: List[Tuple[str, Box]] = [("image", _union(g)) for g in _clusters(images, GAP)] if images else []
    runs = _text_runs(textpage) if paths else []
    for g in _clusters(paths, GAP):
        box = _union(g)
        share = _area(box) / size
        bw, bh = box[2] - box[0], box[3] - box[1]
        if len(g) < DRAW_PATHS or not DRAW_MIN <= share <= DRAW_MAX or bw < 0.1 * w or bh < 0.04 * h \
                or not 1 / 8 <= bw / bh <= 8:
            continue
        if box[0] < 1.5 or box[1] < 1.5 or box[2] > w - 1.5 or box[3] > h - 1.5:
            continue
        lines = sum(1 for b in g if min(b[2] - b[0], b[3] - b[1]) < LINE_MAX)
        words = _words(textpage, box)
        if lines > 0.8 * len(g) and words > 12:
            continue
        if words > 18 + 220 * share or _running_text(runs, box):
            continue
        out.append(("drawing", _with_labels(box, runs, w, h)))
    return out


def _with_labels(box: Box, runs: List[Box], w: float, h: float) -> Box:
    near = (box[0] - 14, box[1] - 14, box[2] + 14, box[3] + 14)
    labels = [r for r in runs if _near(r, near, 0) and r[2] - r[0] <= 0.15 * w and r[3] - r[1] <= 0.06 * h
              and not any(o is not r and abs(o[1] - r[1]) < 2 and 0 <= o[0] - r[2] < 6 for o in runs)]
    return _union([box, *labels]) if labels else box


def page_pictures(pdf: Path, pages: Optional[List[int]] = None) -> Dict[int, List[Tuple[str, Box]]]:
    import pypdfium2 as pdfium

    out: Dict[int, List[Tuple[str, Box]]] = {}
    doc = pdfium.PdfDocument(str(pdf))
    try:
        for i in range(len(doc)):
            if pages and i + 1 not in pages:
                continue
            page = doc[i]
            tp = page.get_textpage()
            try:
                items = _page_pictures(page, tp)
            finally:
                tp.close()
                page.close()
            if items:
                out[i + 1] = items
    finally:
        doc.close()
    return out


def crop_box(boxes: List[Box], width: float, height: float, score: Optional[Any] = None) -> Optional[Box]:
    if not boxes:
        return None
    groups = [_union(g) for g in _clusters(list(boxes), FIGURE_GAP)]
    box = max(groups, key=_area)
    if score and len(groups) > 1:
        rated = sorted(((score(b), _area(b), b) for b in groups), reverse=True)
        if rated[0][0] == 0 or rated[0][0] == rated[1][0]:
            return None
        box = rated[0][2]
    if _area(box) / (width * height) > CROP_MAX:
        return None
    return (max(0.0, box[0] - MARGIN), max(0.0, box[1] - MARGIN), min(width, box[2] + MARGIN),
            min(height, box[3] + MARGIN))


def figure_image(page: Any, box: Box, dest: Path, dpi: int = 200) -> None:
    w, h = page.get_width(), page.get_height()
    bitmap = page.render(scale=dpi / 72.0, crop=(box[0], box[1], w - box[2], h - box[3]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    bitmap.to_pil().save(dest)


def parse_pages(spec: Optional[str]) -> Optional[List[int]]:
    if not spec:
        return None
    pages: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return pages


def find_figures(pdf: Path, out_dir: Path, dpi: int = 200, pages: Optional[List[int]] = None) -> Dict[str, Any]:
    import pypdfium2 as pdfium

    found = page_pictures(pdf, pages)
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72.0
    figures: List[Dict[str, Any]] = []
    doc = pdfium.PdfDocument(str(pdf))
    try:
        total = len(doc)
        for page_no in sorted(found):
            items = found[page_no]
            page = doc[page_no - 1]
            try:
                w, h = page.get_width(), page.get_height()
                groups = _clusters([b for _, b in items], FIGURE_GAP)
                groups.sort(key=lambda g: (-round(_union(g)[3]), _union(g)[0]))
                for n, group in enumerate(groups, 1):
                    box = crop_box(group, w, h)
                    full_page = box is None
                    box = box or (0.0, 0.0, w, h)
                    kinds = sorted({k for k, b in items if b in group})
                    name = "p%03d_f%d.png" % (page_no, n)
                    figure_image(page, box, out_dir / name, dpi)
                    x, y = round(box[0] * scale), round((h - box[3]) * scale)
                    cw, ch = round((box[2] - box[0]) * scale), round((box[3] - box[1]) * scale)
                    figures.append({
                        "page": page_no,
                        "index": n,
                        "kind": kinds[0] if len(kinds) == 1 else "mixed",
                        "full_page": full_page,
                        "box_pt": [round(v, 1) for v in box],
                        "box_px": {"x": x, "y": y, "W": cw, "H": ch},
                        "file": name,
                        "pdftoppm": "pdftoppm -png -r %d -f %d -l %d -x %d -y %d -W %d -H %d SOURCE.pdf fig_p%d"
                                    % (dpi, page_no, page_no, x, y, cw, ch, page_no),
                    })
            finally:
                page.close()
    finally:
        doc.close()
    summary = {
        "source": str(pdf),
        "pages": total,
        "dpi": dpi,
        "figure_pages": sorted(found),
        "figures": figures,
    }
    (out_dir / "figures.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Find and crop the figures on the pages of a PDF.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--pages", help="e.g. 3-7,9")
    args = ap.parse_args(argv)
    try:
        import pypdfium2
    except ImportError:
        print("pypdfium2 is missing: pip install pypdfium2", file=sys.stderr)
        return 2
    try:
        summary = find_figures(args.pdf, args.out_dir, args.dpi, parse_pages(args.pages))
    except Exception as exc:
        print("Could not read %s: %s" % (args.pdf, exc), file=sys.stderr)
        return 1
    figs = summary["figures"]
    print("%d figures on %d of %d pages -> %s" % (len(figs), len(summary["figure_pages"]), summary["pages"],
                                                  args.out_dir / "figures.json"))
    for f in figs:
        print("p%d f%d %s%s %dx%d %s" % (f["page"], f["index"], f["kind"], " full-page" if f["full_page"] else "",
                                         f["box_px"]["W"], f["box_px"]["H"], f["file"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
