import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "lectoprint", "scripts"))
import doc_builder as db
import practice

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Lectoprint_TR_Soru_Bankasi.pdf")
d = db.Doc(OUT, "Lectoprint örneği · Sonlu Otomatlar: NFA → DFA · Soru bankası (TR)", "Sonlu Otomatlar: NFA'dan DFA'ya", "Lectoprint", lang="tr")
d.cover(["Sonlu Otomatlar", "NFA → DFA"], "Soru bankası ve model cevaplar",
        ["Mod: Tamamen Türkçe", "İçerik: yalnızca sorular, 15 / 15 / 15 / 15", "Kaynak: bu örnek için yazılmış özgün notlar"], "LECTOPRINT")
d.toc([("1", "Sınav Pratiği"), ("2", "Sınav Kritik Noktaları Özeti")])
practice.practice(d, "1", "tr", (15, 15, 15, 15), db.PRIMARY)
practice.summary(d, "2", "tr", db.SUMMARY)
d.build()
print(OUT)
