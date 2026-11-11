import re
import subprocess
import sys

ASCII_TR = ["Donusum", "donusum", "Adim", "adim", "icin", "cunku", "Sinav", "sinav", "Ozet", "ozet", "Tanim", "tanim", "Dogru", "Yanlis", "degil"]
EN_WORDS = ["the", "and", "which", "state", "states", "string", "answer", "true", "false", "subset", "closure"]


def run(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout


def check(path, lang):
    errors = []
    fonts = run("pdffonts", path).splitlines()[2:]
    for line in fonts:
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
    pages = int(re.search(r"Pages:\s+(\d+)", run("pdfinfo", path)).group(1))
    return pages, errors


if __name__ == "__main__":
    failed = False
    for arg in sys.argv[1:]:
        path, lang = arg.rsplit(":", 1)
        pages, errors = check(path, lang)
        print("%s [%s] %d pages: %s" % (path, lang, pages, "OK" if not errors else "FAIL"))
        for e in errors:
            print("   - " + e)
        failed |= bool(errors)
    sys.exit(1 if failed else 0)
