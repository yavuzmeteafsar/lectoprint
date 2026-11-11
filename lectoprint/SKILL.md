---
name: lectoprint
description: "Turns slides or notes into an exam-ready study PDF: full notes, quick review or question bank; English, hybrid TR+EN or Turkish. Use for study PDF, ders PDF'i, sınav notu, hızlı tekrar."
dependencies: python>=3.8, reportlab>=4.0, matplotlib>=3.7
---

# Lectoprint

Lectoprint produces one kind of output: a printable study PDF built from the user's course material, with the reasoning flow **why → example → question**, not memorisation. Everything the skill needs is in this file plus `scripts/doc_builder.py` next to it.

The goal: nothing in the source is skipped, every claim is traceable to a slide or page, and the PDF works as the last thing a student reads before an exam.

## 1. Start: ask once, then work

Before writing anything, ask the four questions below **in a single message**. Skip any question the user's request already answers ("make me a Turkish question PDF" answers 1 and 2). If the user says "you decide", use the defaults.

1. **Language mode** — "The default is English. Would you like hybrid (Turkish explanations with the English originals) or fully Turkish instead?" Default: `en`.
2. **Content type** — "Full lecture notes, a quick review, or questions only?" Default: full.
3. **Questions at the end** — only if the answer to 2 is *full lecture notes*: "Should I add the exam practice section at the end?" Default: yes. Quick review always includes questions; do not ask.
4. **Figures** — only if the source contains slides or PDF pages with figures: "Should I include figures from the slides as screenshots?" Default: yes. Do not ask when the source is only the chat.

If the answer to 4 is **no**, tell the user in one sentence before starting, in the chosen language: *"No screenshots will be added. Figures that can be redrawn exactly (automata, graphs, networks) will still be drawn; for the rest the caption points to the source page."*

Also settle, usually from context without asking:
- **Topic title** — used on the cover, footer and file name.
- **Source** — uploaded files, project files, or this conversation. If the source is the conversation, carry every subtopic, question and example from it into the PDF.
- **Subject style** (mix if needed): conceptual/theoretical, programming, commands/workflow, exam preparation for a specific quiz (Section 6).

## 2. Language modes

| | `en` (default) | `hybrid` | `tr` |
|---|---|---|---|
| Explanations | English | Turkish | Turkish |
| Source quotes (`src_box`) | Original only | Original English, then Turkish translation | Turkish only (translated if the source is English) |
| Technical terms | English | Kept in English; Turkish in parentheses at first definition | Turkish; English in parentheses at first definition |
| Questions and model answers | English | English (explanations around them in Turkish) | Turkish |
| Fixed labels (WARNING, Page, Contents…) | English | Turkish | Turkish |

Pass the mode to the builder: `Doc(..., lang="en" | "hybrid" | "tr")`. The builder switches the fixed labels; you write the content in the right language.

### 2.1 Terms

- **en**: use the source's terms as they are.
- **hybrid**: never translate a technical term that appears in English in the source. At its **first definition** add the Turkish in parentheses — "nondeterministic finite automaton (deterministik olmayan sonlu otomat)". After that, keep the English term even inside Turkish sentences — "Bu NFA'nın transition function'ı…", "ε-closure'u al". Do not repeat the parenthesis later.
- **tr**: the reverse. Use the established Turkish term and give the English once, at the first definition — "deterministik olmayan sonlu otomat (nondeterministic finite automaton, NFA)". Acronyms (NFA, DFA, CPU, SQL) stay as they are. If the source is already Turkish, quote it directly and add nothing.

### 2.2 Turkish text (hybrid and tr)

- Write real Turkish characters everywhere: ç ğ ı İ ö ş ü Ç Ğ Ö Ş Ü — cover, headings, table headers, box titles, captions.
- Upper case: i → İ, ı → I. Python's `.upper()` gets this wrong; write upper-case headings by hand.
- Suffixes after an apostrophe follow pronunciation: NFA'nın, DFA'yı, 3'ün, A'nın, C'nin.
- Text uses only the DejaVu fonts registered by the builder. Built-in PDF fonts (Helvetica, Times) cannot draw ğ ı İ ş.

### 2.3 All modes

- No Unicode sub/superscript characters (₀₁²); use `<sub>` and `<super>`. Symbols like ε δ Σ ∅ → ∪ draw directly.
- Display maths (integrals, sums, fractions, Greek-heavy formulas) go through `math()`, which renders LaTeX-style mathtext. `formula()` stays for step-by-step plain-text calculations and tables of values. It supports a LaTeX subset (matplotlib mathtext): no `\iff`, `\text{}` or matrices. Use `\Leftrightarrow`, `\mathrm{}`, and put matrices in a `grid()`. A parse error names the failing line.

## 3. Source discipline

- Use only the methods shown in the source (slides, book, recitations). Do not switch to an outside method the instructor may not accept.
- Quote definitions, theorems and question texts **verbatim** from the source and label them ("Week 4, slide 8", "Recitation 2 – Q1").
- Label everything that is not in the source: your own questions are **Original question**, filled-in gaps are **Assumption**. If the source says a result is "not shown here", say so and mark the solution as yours.
- If the source has a typo (wrong state name, missing brace), write the correct version and flag it in a `warn_box`.

## 4. Content types

### 4.1 Full lecture notes

Each topic section, in this order:

1. **What and why** — what the concept is, why it exists, how it connects to the previous one. Explanatory sentences, not terse bullets.
2. **Source definition** — `src_box`.
3. **Definition table** — `def_tbl` for concepts, parameters, flags.
4. **Examples** — every example in the source, none skipped. First the original text (`src_box` or `q_box`), then the solution.
5. **Step-by-step solution** — each step under its own `h3`. One operation per step; every intermediate result in a `grid` or `formula`/`math` box. Never jump to "the result is…"; show where each cell comes from.
6. **Figure** — if the source has a figure for this topic, it goes in before the solution (Section 5).
7. **Boxes** — traps in `warn_box`, shortcuts in `tip_box`, source comparisons in `info_box`.

After the topic sections: **Glossary**, then **Exam Practice** (if requested), then the **Key Points Summary** last (Section 4.4).

Style notes:
- **Programming**: explain what a code block will do before it, then walk through it line by line after it. No comments inside code blocks; the explanation lives outside. Parameters go in a `def_tbl`.
- **Commands/workflow**: before each command its purpose, then its flags in a table. Build a scenario: "you ran X, then Y, the result is Z". Show error output in its own block; lines starting with `!!` are drawn red.
- **Conceptual**: an analogy first, derivations step by step, and for each diagram say what it represents.

### 4.2 Quick review

For the night before the exam. The lecture part is about one third the length of full notes. Per topic:

- **Keep**: a 1–2 paragraph "what and why"; the main definitions in `src_box` (secondary ones go to the glossary); **one** worked example — the most representative one in the source — with its steps collected in a single `grid` or `formula`/`math` box instead of separate `h3` steps; **all** `warn_box` and `tip_box` content.
- **Drop**: second and later examples, separate `h3` step headings, analogies, long derivations.
- **Figures**: only the ones that belong to the kept example.

Then the Glossary (including the confused-pairs table), Exam Practice with the quick-review counts, and the Key Points Summary.

### 4.3 Questions only

A short cover and contents page, then straight into Exam Practice with the questions-only counts, then the Key Points Summary. No lecture sections and no glossary.

### 4.4 Glossary, Exam Practice and Summary

**Glossary** — `sec_hdr(no, title, bg=PRIMARY)`; title: *Glossary* / *Tanım Sözlüğü*.
- A short intro: definitions are verbatim from the source; bold words are the keywords an answer must contain.
- `info_box` "How to study this section": (1) read the term and say the definition in your own words, (2) compare with the definition and find the bold word you missed, (3) ask why that word is there. Give a concrete example from the topic.
- Every concept defined in the source, in source order, in one `grid`. Headers by mode — en: `["Term", "Definition", "Source"]`; hybrid: `["Term", "Definition (kaynaktaki İngilizce)", "Kaynak"]`; tr: `["Terim", "Tanım", "Kaynak"]`. Widths `[1.6, 4.6, 0.6]`, `mono_cols=[2]`. Distinguishing keywords in `<b>`. For concepts with drawing rules (e.g. UML relationships), include the rule.
- Subsection **Commonly confused pairs** (*Karıştırılan tanım çiftleri*): `["Pair", "Distinguishing point"]` / `["Çift", "Ayırt edici nokta"]`, written as `<i>A</i> vs <i>B</i>` using the source's own words. Put `d.add(CondPageBreak(9 * cm))` before it.

**Exam Practice** — `sec_hdr(no, title, bg=PRIMARY)`; title: *Exam Practice* / *Sınav Pratiği*. Fixed counts, regardless of how long the source is:

| Content type | True/False | Multiple choice | Open-ended (of which scenario) | Definition |
|---|---|---|---|---|
| Full lecture notes | 12 | 10 | 6 (2–3) | 10 |
| Quick review | 8 | 8 | 3 (1) | 8 |
| Questions only | 15 | 15 | 15 (6) | 15 |

- Start with an `info_box` "Note": whether the source has its own question bank, and that the questions here are Original.
- **True / False**: `q_box("T/F n", statement)` + `hl_box("<b>True/False.</b> short reason (slide n)")`. Balance True and False. Build false statements from the source's typical traps (numbers, line types, direction, "only one", "always").
- **Multiple choice**: `q_box("MC n", [question, "a) …", "b) …", "c) …", "d) …"])` + `hl_box("<b>Answer: x.</b> reason (slide n)")`. Include "which is NOT" and interpretation questions; spread the correct letters.
- **Open-ended**: `q_box("OE n" or "OE n (Scenario)", question)` + `hl_box([paragraphs], title="Model answer")`. Scenario questions ask for a diagram, model or decision for a given system, answered only with the source's notation.
- **Definition questions**: first an `info_box` "How to answer": write the source's definition with its keywords, then add an example or drawing rule from the source. Then `q_box("Definition n", "Define X / Distinguish X from Y")` + `hl_box(answer, title="Model answer")`. Choose the most important definitions or pairs; scoring keywords in bold.
- Keep each question with its answer: before each `q_box` add `d.add(CondPageBreak(...))` — T/F 3.5 cm, MC and Definition 6 cm, Open-ended 9 cm.
- Every answer rests only on source definitions and cites a slide or page.
- In `tr` mode labels become "D/Y n", "ÇS n", "AU n" / "AU n (Senaryo)", "Tanım n"; answer lines "Doğru/Yanlış", "Cevap: x", title "Model cevap".
- **Write each question type in its own file** (`part_tf.py`, `part_mc.py`, `part_oe.py`, `part_def.py`) and run them from `build.py`. Large banks do not fit in one response; splitting keeps every file complete.

**Key Points Summary** — always the last section, `sec_hdr(no, title, bg=SUMMARY)`; title: *Key Exam Points* / *Sınav Kritik Noktaları Özeti*. One `hl_box` per point.

## 5. Figures

Every figure in the source must appear in the PDF, unless the user said no to figures. Describing a figure only in words loses direction, sign and label information.

- **Redraw** with `diagram()` when it can be reproduced exactly (automata, state diagrams, directed networks, simple graphs). Node names, arrow directions, labels and known/unknown distinctions must match the source.
- **Screenshot** everything else (circuits, function plots, curves, geometry, photos, complex illustrations, tables drawn as images) with `image()`. If unsure, screenshot; an approximate redraw is worse than a correct screenshot.
- **Cropping**: render the page at low resolution to locate the figure, then crop only the figure at high resolution: `pdftoppm -png -r 200 -f N -l N -x X -y Y -W W -H H source.pdf fig_sN` (X, Y, W, H in 200-dpi pixels). Open the crop and check that labels, arrows and values are all inside and no extra text is. Convert `.pptx` sources first with `soffice --headless --convert-to pdf`.
- **Placement**: right after the `q_box`/`src_box` of the example it belongs to, before the solution steps. Repeat it if the solution needs it again.
- **Caption**: source and page — "Source: Week 4 Workbook, p.4 (screenshot)" or "(redrawn)".
- **Reading check**: verify everything read off a figure (polarity, arrow direction, axis values) by looking closely. If it is ambiguous, say so in a `warn_box` as an Assumption and include the screenshot anyway.
- If the user said **no** to figures: redraw what `diagram()` can reproduce; for the rest write a caption-style line "See source, p.N" where the figure would have been.
- Never invent figures. An extra explanatory drawing gets the caption "Not in the source, added for explanation".

## 6. Exam preparation for a specific quiz

When the user is preparing for a specific quiz (for example a question a friend described):

1. **Section 0 – What we know**: tabulate the known facts (machine, requirements, unknowns). If the description is ambiguous, list the possible readings and say which one you take as primary.
2. **Closest questions in the sources**: pick the slide examples and recitation questions closest to the description. For each, a "Why this question?" paragraph linking it to the exam, then a full step-by-step solution.
3. **Original question**: write the closest question in the source's format and solve every part. If ambiguous, add a variant for the other reading.
4. Conceptual sub-questions get an explanation based on the source's sentences and a **model answer** in an `hl_box`.
5. If there was an earlier quiz, explain the difference in an `info_box`.

## 7. Verification

- Every result that involves calculation or an algorithm (conversion tables, traces, numeric answers, code output) is computed by a separate script and compared before it goes into the PDF. When you describe a language, test all short strings with a script.
- Code examples that can run are actually run.

## 8. Build

1. Find the builder that ships with this skill: `find / -path /proc -prune -o -name doc_builder.py -path "*lectoprint*" -print 2>/dev/null`. It sits in `scripts/` next to this SKILL.md. Create a working folder (e.g. `./lectoprint_<topic>/`) and copy it there **unchanged**; add new methods only if needed.
   If it is not found, the skill was installed without its `scripts/` folder (usually SKILL.md was uploaded on its own). Do not rewrite the builder from memory and do not ask the user for a folder. Tell the user in one sentence to reinstall from `lectoprint.zip` (https://github.com/yavuzmeteafsar/lectoprint/releases/latest), then stop.
2. Write the content in `build.py` (and the `part_*.py` files) by calling `Doc` methods in order. Files are UTF-8.
3. `python3 build.py`.

### Doc API

| Method | Purpose |
|---|---|
| `Doc(path, footer_text, title, author, lang)` | The document. `lang`: `"en"` (default), `"hybrid"`, `"tr"`. `footer_text` is printed on every page. |
| `cover(title_lines, sub, info_lines, bottom)` | Cover page. 1–3 title lines. |
| `toc([(no, title), ...])` | Contents page. |
| `sec_hdr(no, text, bg=DEEP)` | Section bar. `bg`: `DEEP` (topic sections), `PRIMARY` (glossary, exam practice, source questions), `PDARK` (original question), `SUMMARY` (key points). |
| `h2`, `h3`, `body`, `bullets([..])`, `sp(h)` | Headings, paragraphs, lists. ReportLab mini-HTML works: `<b>`, `<i>`, `<sub>`, `<super>`, `<font color>`. |
| `src_box(orig, tr=None, src)` | Source quote. `orig` is the original text, `tr` its Turkish translation; the builder shows what the mode requires. String or list. |
| `q_box(label, lines)` | Question box. |
| `info_box(title, text)`, `warn_box(text)`, `tip_box(text)`, `hl_box(text, title)` | Coloured boxes; `text` is a string or a list of paragraphs. |
| `formula(lines)` | Monospace box for step-by-step calculations. |
| `math(lines, fs=13)` | Display maths: each line is a LaTeX mathtext string (`r"\int_0^1 x^2\,dx = \frac{1}{3}"`). |
| `def_tbl([(left, right), ...], w0)` | Two-column definition table. |
| `grid(header, rows, widths, mono_cols, hl_rows, red_rows, green_rows, caption)` | General table. Row colours: hl yellow (attention), red (rejected/error), green (accepted/correct). |
| `code_block_hl(code, lang, label)` | Dark+ highlighted code. `lang`: python, java, c, cpp, javascript, sql, bash, matlab, verilog, vhdl; anything else is uncoloured. Lines starting with `!!` are red. Long blocks split across pages. |
| `diagram(w, h, states, edges, caption)` | State diagram / directed network (below). |
| `image(path, width_frac, caption)` | Cropped figure or screenshot; `width_frac` of the text width (default 0.75), shrunk to fit the page height. |
| `page_break()`, `build()` | Page break, write the PDF. |

### Diagrams

- `states`: list of `(name, x, y, flags)`. flags: `("start",)`, `("acc",)`, `("start", "acc")`, `()`, or `{"start": 1, "sdir": 215}` to set the start arrow direction in degrees (default 180 = from the left).
- `edges`: `dict(s=source, d=target, l=label, bend=curvature, lp=label position 0–1, off=label offset, ang=loop direction)`.
- For a pair of opposite arrows give both the same positive `bend` (10–16); they separate into two arcs.
- A loop (`s == d`) puts its label about 45 pt from the node; near the edge of the box turn the loop inward with `ang` or increase `h`.
- Use `lp` (0.25–0.4) on crossing edges to keep labels apart. Check every diagram in the preview.

## 9. Check and deliver

1. Preview: `pdftoppm -png -r 60 out.pdf prev/pg`, combine pages into sheets of six with PIL and look at each. Look at diagram and table-heavy pages at `-r 110`. Check for overflowing text, broken tables, overlapping diagram labels, loop labels outside their box, empty pages. **Figure check**: count the figures in the source and confirm each one is in the PDF (drawn, screenshot, or "see source" line), and that crops are complete and legible.
2. Language check: `pdffonts out.pdf` must list only embedded DejaVu fonts for text. In hybrid and tr modes `pdftotext out.pdf -` must not contain ASCII-flattened Turkish such as "Donusum", "Adim", "icin", "cunku". In tr mode there must be no untranslated English sentences outside acronyms and the parenthesised first definitions.
3. Fix and rebuild if needed.
4. Copy the PDF to the outputs folder with a meaningful name (e.g. `Automata_NFA_to_DFA_QuickReview.pdf`) and send it to the user.
5. In the reply, state only the page count, the sections covered and any assumptions. Do not repeat the content.
