# Third-party notices

## IEUStudia

`lectoprint/scripts/find_figures.py` is adapted from `src/studia/outputs/figures.py` in
[IEUStudia](https://github.com/mirzaisi/IEUStudia) (version 4.1.2, commit `23d7bd1`), used with the
author's permission ([IEUStudia issue #5](https://github.com/mirzaisi/IEUStudia/issues/5)).

Changes from the original: the figure-finding part only (no Markdown/HTML helpers); no cache, lock or
application imports; a command-line interface that writes one PNG per figure and a JSON summary; figures
far apart on a page are cropped separately and numbered in reading order; a path counts as a line when it
is under 2.5 pt thick instead of 1.5 pt, because pdfium rounds object bounds outward to whole points;
images that render as a single colour (covered by a white box) are skipped; identical crops are marked as
duplicates; rotated pages are cropped in the orientation they are displayed in.

```
MIT License

Copyright (c) 2026 IEUStudia contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
