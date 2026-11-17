import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lectoprint" / "scripts"))
import doc_builder as db


def orphans(tmp, before_heading):
    found = []
    for gap in range(0, 22):
        out = os.path.join(tmp, "o.pdf")
        d = db.Doc(out, "T", "T", "", lang="en")
        d.sp(500 + gap * 10)
        if before_heading:
            d.add(db.CondPageBreak(before_heading * db.cm))
        d.h2("11.3 Open-ended")
        d.add(db.CondPageBreak(9 * db.cm))
        d.q_box("OE 1", "Question text " * 20)
        d.hl_box(["answer " * 40], title="Model answer")
        d.build()
        first = subprocess.run(["pdftotext", out, "-"], capture_output=True, text=True, check=True).stdout.split("\f")[0]
        if "Open-ended" in first and "OE 1" not in first:
            found.append(gap)
    return found


def main():
    with tempfile.TemporaryDirectory() as tmp:
        without = orphans(tmp, None)
        with_rule = orphans(tmp, 10)
        print("orphaned heading without the rule at", without, "with it at", with_rule)
        assert without, "the test no longer reproduces an orphaned heading"
        assert not with_rule, with_rule
        print("layout rules: OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
