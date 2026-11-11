import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "lectoprint", "scripts"))
import doc_builder as db
import bank
import figs
import practice

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Lectoprint_Hybrid_Quick_Review.pdf")
d = db.Doc(OUT, "Lectoprint örneği · Finite Automata: NFA → DFA · Hızlı tekrar (TR+EN)", "Finite Automata: NFA to DFA", "Lectoprint", lang="hybrid")
d.cover(["Finite Automata", "NFA → DFA"], "Sınav öncesi hızlı tekrar",
        ["Mod: Hibrit (Türkçe açıklama + İngilizce orijinal)", "İçerik: kısa konu anlatımı + 8 / 8 / 3 / 8 soru", "Kaynak: bu örnek için yazılmış özgün notlar"], "LECTOPRINT")
d.toc([("1", "DFA ve NFA"), ("2", "Subset Construction"), ("3", "Tanım Sözlüğü"), ("4", "Sınav Pratiği"), ("5", "Sınav Kritik Noktaları Özeti")])

d.sec_hdr("1", "DFA ve NFA")
d.h2("1.1 Ne ve neden")
d.body("Deterministic finite automaton (deterministik sonlu otomat), girdisini sembol sembol okuyan ve her adımda <b>tam olarak bir</b> sonraki duruma geçen bir makinedir. "
       "Nondeterministic finite automaton (deterministik olmayan sonlu otomat) ise bir sembolle birden fazla duruma ya da hiçbir duruma gidebilir; NFA, çalışmalarından <b>en az biri</b> kabul durumunda bitiyorsa string'i kabul eder. "
       "NFA tasarlaması kolaydır, DFA çalıştırması kolaydır; bu bölümün amacı ikisi arasında köprü kurmaktır.")
d.src_box("A DFA is a 5-tuple (Q, Σ, δ, q<sub>0</sub>, F) where δ : Q × Σ → Q is the transition function.",
          "DFA, geçiş fonksiyonu δ : Q × Σ → Q olan bir (Q, Σ, δ, q<sub>0</sub>, F) 5'li demetidir.", bank.ref("en", 1))
d.src_box("An NFA is defined like a DFA, except that δ : Q × Σ → P(Q). The NFA accepts w if at least one run on w ends in a state of F.",
          "NFA, DFA gibi tanımlanır; farkı δ : Q × Σ → P(Q) olmasıdır. NFA, w üzerindeki en az bir çalışma F'deki bir durumda bitiyorsa w'yi kabul eder.", bank.ref("en", 2))
d.warn_box("F = ∅ olan bir DFA hiçbir şeyi kabul etmez, boş string ε'u bile. NFA'da ise bir yolun \"ölmesi\" string'in reddedildiği anlamına gelmez; başka bir yol kabul edebilir.")

d.sec_hdr("2", "Subset Construction")
d.h2("2.1 Ne ve neden")
d.body("Subset construction (alt küme yapısı), NFA'nın tahminlerini ortadan kaldırır: DFA, NFA'nın <b>o anda içinde olabileceği bütün durumların kümesini</b> tek bir durum olarak tutar. "
       "Bu yüzden DFA'nın her durumu bir NFA durum kümesidir; bir sonraki küme, kümedeki durumların gidebileceği her yerin birleşimidir.")
d.src_box("The subset construction builds a DFA whose states are subsets of Q<sub>N</sub>, with start state {q<sub>0</sub>}, transitions δ<sub>D</sub>(S, a) = ∪<sub>p∈S</sub> δ<sub>N</sub>(p, a), and accepting states all S with S ∩ F<sub>N</sub> ≠ ∅.",
          "Subset construction, durumları Q<sub>N</sub>'nin alt kümeleri olan bir DFA kurar: başlangıç durumu {q<sub>0</sub>}, geçişler δ<sub>D</sub>(S, a) = ∪<sub>p∈S</sub> δ<sub>N</sub>(p, a), kabul durumları ise S ∩ F<sub>N</sub> ≠ ∅ olan bütün S'ler.", bank.ref("en", 3))
d.math([r"\delta_D(S,a)=\bigcup_{p\in S}\delta_N(p,a),\qquad |Q_D|\leq 2^{|Q_N|}"])
d.h2("2.2 Çözümlü örnek")
d.q_box("Example (source, p.3)", "Convert the NFA below, which accepts the strings over {0, 1} that end in 01, to a DFA. Build only the reachable states.")
d.diagram(390, 105, figs.NFA_STATES, figs.NFA_EDGES, "Kaynak: Örnek notlar, s.2 (yeniden çizim)")
d.body("{q<sub>0</sub>}'dan başlanır ve her yeni küme için iki sembol denenir; yeni küme çıkmayınca durulur. Bütün adımlar tek tabloda:")
d.grid(["Küme S", "δD(S, 0)", "δD(S, 1)", "Not"],
       [("→ {q0}", "{q0} → {q0, q1}", "{q0}", "{q0, q1} yeni"),
        ("{q0, q1}", "{q0, q1} ∪ ∅ = {q0, q1}", "{q0} ∪ {q2} = {q0, q2}", "{q0, q2} yeni"),
        ("* {q0, q2}", "{q0, q1} ∪ ∅ = {q0, q1}", "{q0} ∪ ∅ = {q0}", "yeni küme yok, dur")],
       widths=[1.3, 2.2, 2.2, 1.6], green_rows=(2,), caption="Subset construction adımları (yeşil: kabul durumu, çünkü q2'yi içerir)")
d.diagram(440, 150, figs.DFA_STATES, figs.DFA_EDGES, "Sonuç DFA")
d.warn_box("2<super>3</super> = 8 sadece üst sınırdır. {q<sub>1</sub>} ya da ∅ burada hiç ulaşılmadığı için DFA'nın durumu değildir; bunları listelemek sık yapılan bir sınav hatasıdır.")
d.tip_box("\"… ile biter\" dilleri için NFA kalıbı: başlangıç durumunda 0, 1 döngüsü ve son ek için bir durum zinciri. Döngü öneki yutar, nondeterminism son ekin nerede başladığını seçer.")
d.tip_box("ε-NFA'da tek fark: başlangıç ε-closure(q<sub>0</sub>) olur ve her geçişten sonra tekrar ε-closure alınır (s.4).")

practice.glossary(d, "3", "hybrid", db.PRIMARY)
practice.practice(d, "4", "hybrid", (8, 8, 3, 8), db.PRIMARY)
practice.summary(d, "5", "hybrid", db.SUMMARY)
d.build()
print(OUT)
