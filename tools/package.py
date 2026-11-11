import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "lectoprint")
DIST = os.path.join(ROOT, "dist")


def check_frontmatter():
    text = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit("SKILL.md has no frontmatter")
    fm = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    name = fm.get("name", "").strip()
    desc = fm.get("description", "").strip().strip('"')
    if name != os.path.basename(SKILL):
        sys.exit("name %r must match the folder name" % name)
    if len(name) > 64:
        sys.exit("name is longer than 64 characters")
    if len(desc) > 200:
        sys.exit("description is %d characters; the limit is 200" % len(desc))


def main():
    check_frontmatter()
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "lectoprint.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(SKILL):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, ROOT))
    print(out)


if __name__ == "__main__":
    main()
