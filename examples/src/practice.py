from reportlab.platypus import CondPageBreak
from reportlab.lib.units import cm
import bank

L = {
    "en": dict(title="Exam Practice", tf="True / False", mc="Multiple Choice", oe="Open-ended", df="Definition Questions",
               tfl="T/F %d", mcl="MC %d", oel="OE %d", oes="OE %d (Scenario)", dfl="Definition %d",
               T="True.", F="False.", ans="Answer: %s.", model="Model answer",
               note=("Note", "The source has no question bank of its own, so every question here is an <b>Original question</b> built from its definitions and examples. Each answer cites the page it rests on."),
               how=("How to answer", "First write the definition with its keywords, then add an example or drawing rule from the source.")),
    "hybrid": dict(title="Sınav Pratiği", tf="True / False", mc="Multiple Choice", oe="Open-ended", df="Definition Questions",
                   tfl="T/F %d", mcl="MC %d", oel="OE %d", oes="OE %d (Scenario)", dfl="Definition %d",
                   T="True.", F="False.", ans="Answer: %s.", model="Model answer (EN)",
                   note=("Not", "Kaynakta hazır bir soru bankası yok; buradaki bütün sorular kaynaktaki tanım ve örneklerden kurulmuş <b>Özgün sorulardır</b>. Sorular ve model cevaplar sınavdaki gibi İngilizcedir; her cevapta dayandığı sayfa yazar."),
                   how=("Nasıl cevaplanır?", "Önce kaynaktaki tanım cümlesini anahtar kelimeleriyle yaz, sonra kaynaktan bir örnek ya da çizim kuralı ekle.")),
    "tr": dict(title="Sınav Pratiği", tf="Doğru / Yanlış", mc="Çoktan Seçmeli", oe="Açık Uçlu", df="Tanım Soruları",
               tfl="D/Y %d", mcl="ÇS %d", oel="AU %d", oes="AU %d (Senaryo)", dfl="Tanım %d",
               T="Doğru.", F="Yanlış.", ans="Cevap: %s.", model="Model cevap",
               note=("Not", "Kaynakta hazır bir soru bankası yok; buradaki bütün sorular kaynaktaki tanım ve örneklerden kurulmuş <b>Özgün sorulardır</b>. Her cevapta dayandığı sayfa yazar."),
               how=("Nasıl cevaplanır?", "Önce tanım cümlesini anahtar kelimeleriyle yaz, sonra kaynaktan bir örnek ya da çizim kuralı ekle.")),
}


TR_TERMS = [
    ("Subset construction'ı (alt küme yapısı)", "Alt küme yapısını (subset construction)"),
    ("subset construction'ın", "alt küme yapısının"), ("subset construction'da", "alt küme yapısında"),
    ("Subset construction'da", "Alt küme yapısında"), ("Subset construction'ın", "Alt küme yapısının"), ("subset construction'ı", "alt küme yapısını"),
    ("Subset construction", "Alt küme yapısı"), ("subset construction", "alt küme yapısı"),
    ("ε-closure'un", "ε-kapanışının"), ("ε-closure'u", "ε-kapanışını"), ("ε-closure", "ε-kapanış"),
    ("closure'larının", "kapanışlarının"), ("closure alınır", "kapanış alınır"),
    ("string'dir", "dizgidir"), ("string'ini", "dizgisini"), ("string'lerin", "dizgilerin"), ("string'ler", "dizgiler"),
    ("string'in", "dizginin"), ("string'i", "dizgiyi"), ("string", "dizgi"),
]
TR_FIRST = [("dizgiyi", "dizgiyi (string)"), ("alt küme yapısı", "alt küme yapısı (subset construction)"),
            ("ε-kapanış(q)", "ε-kapanış(q) (ε-closure)")]


def tr_fix(x, seen):
    if isinstance(x, list):
        return [tr_fix(i, seen) for i in x]
    for a, b in TR_TERMS:
        x = x.replace(a, b)
    for a, b in TR_FIRST:
        if a not in seen and a in x:
            x = x.replace(a, b, 1); seen.add(a)
    return x


def practice(d, no, lang, counts, bg):
    s = L[lang]
    seen = set()
    fx = (lambda v: tr_fix(v, seen)) if lang == "tr" else (lambda v: v)
    t = lang == "tr"
    pg = "s." if t else "p."
    n_tf, n_mc, n_oe, n_df = counts
    d.sec_hdr(no, s["title"], bg=bg)
    d.info_box(*s["note"])
    d.h2("%s.1 %s (%d)" % (no, s["tf"], n_tf))
    for i, (en, tr, ok, ren, rtr, p) in enumerate(bank.TF[:n_tf], 1):
        d.add(CondPageBreak(3.5 * cm))
        d.q_box(s["tfl"] % i, fx(tr) if t else en)
        d.hl_box("<b>%s</b> %s (%s%d)" % (s["T"] if ok else s["F"], fx(rtr) if t else ren, pg, p))
    d.h2("%s.2 %s (%d)" % (no, s["mc"], n_mc))
    for i, (qen, qtr, oen, otr, a, ren, rtr, p) in enumerate(bank.MC[:n_mc], 1):
        opts = otr if t else oen
        d.add(CondPageBreak(6 * cm))
        d.q_box(s["mcl"] % i, [fx(qtr) if t else qen] + ["%s) %s" % (k, fx(o) if t else o) for k, o in zip("abcd", opts)])
        d.hl_box("<b>%s</b> %s (%s%d)" % (s["ans"] % a, fx(rtr) if t else ren, pg, p))
    d.h2("%s.3 %s (%d)" % (no, s["oe"], n_oe))
    for i, (qen, qtr, sc, aen, atr, p) in enumerate(bank.OE[:n_oe], 1):
        d.add(CondPageBreak(9 * cm))
        d.q_box((s["oes"] if sc else s["oel"]) % i, fx(qtr) if t else qen)
        d.hl_box(fx(atr) if t else aen, title=s["model"])
    d.h2("%s.4 %s (%d)" % (no, s["df"], n_df))
    d.info_box(*s["how"])
    for i, (qen, qtr, aen, atr) in enumerate(bank.DEF[:n_df], 1):
        d.add(CondPageBreak(6 * cm))
        d.q_box(s["dfl"] % i, fx(qtr) if t else qen)
        d.hl_box(fx(atr) if t else aen, title=s["model"])


def summary(d, no, lang, bg):
    d.sec_hdr(no, "Key Exam Points" if lang == "en" else "Sınav Kritik Noktaları Özeti", bg=bg)
    seen = set()
    for en, tr in bank.SUMMARY:
        d.hl_box(en if lang == "en" else (tr_fix(tr, seen) if lang == "tr" else tr))


def glossary(d, no, lang, bg):
    from reportlab.platypus import CondPageBreak as CPB
    en = lang == "en"
    d.sec_hdr(no, "Glossary" if en else "Tanım Sözlüğü", bg=bg)
    if en:
        d.body("Definitions follow the source. <b>Bold</b> words are the keywords an exam answer must contain.")
        d.info_box("How to study this section", "(1) Read the term and say the definition in your own words. (2) Compare with the table and find the bold word you missed. (3) Ask why that word is there: for a DFA, why must δ be <b>total</b>? Because a DFA has to know its next state for every symbol.")
        hdr = ["Term", "Definition", "Source"]
    else:
        d.body("Tanımlar kaynaktan birebir alınmıştır. <b>Kalın</b> kelimeler, cevapta mutlaka geçmesi gereken anahtar kelimelerdir.")
        d.info_box("Bu bölüm nasıl çalışılır? (ezber değil, mantık)", "(1) Terimi oku, tanımı kendi cümlenle söyle. (2) Tabloya bak, atladığın kalın kelimeyi bul. (3) O kelimenin neden orada olduğunu sor: DFA'da δ neden <b>tam</b> olmalı? Çünkü DFA her sembol için bir sonraki durumunu bilmek zorunda.")
        hdr = ["Term", "Definition (kaynaktaki İngilizce)", "Kaynak"]
    d.grid(hdr, [(a, b, c) for a, b, _, c in bank.GLOSSARY], widths=[1.6, 4.6, 0.9], mono_cols=[2])
    d.add(CPB(9 * cm))
    d.h2("Commonly confused pairs" if en else "Karıştırılan tanım çiftleri")
    d.grid(["Pair", "Distinguishing point"] if en else ["Çift", "Ayırt edici nokta"],
           [(a, b if en else c) for a, b, c in bank.PAIRS], widths=[2, 4.8], mono_cols=[])
