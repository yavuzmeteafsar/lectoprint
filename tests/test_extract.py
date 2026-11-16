import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "lectoprint" / "scripts"))
import extract
import test_find_figures


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "deck.pdf")
        test_find_figures.build(pdf, tmp)
        out = Path(tmp) / "src"
        s, warning = extract.extract(Path(pdf), out)
        info = {p["page"]: p["reasons"] for p in s["page_info"]}
        print(info, warning)
        assert warning is None, warning
        assert info[1] == [], info
        assert info[5] == ["little text", "figure"], info
        assert info[2] == ["little text", "figure"] or info[2] == ["figure"], info
        assert set(s["figure_pages"]) == set(test_find_figures.EXPECTED), s["figure_pages"]
        text = (out / "source.txt").read_text(encoding="utf-8")
        assert "=== Page 2 ===\nSeries RC circuit" in text, text[:300]
        assert sorted(os.listdir(out / "look")) == ["p%03d.png" % p for p in s["little_text"]]
        assert json.loads((out / "pages.json").read_text())["min_chars"] == 200
        s2, _ = extract.extract(Path(pdf), Path(tmp) / "src2", min_chars=10, render=False)
        assert len(s2["little_text"]) < len(s["little_text"]), (s2["little_text"], s["little_text"])
        print("extract: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
