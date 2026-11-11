NFA_STATES = [("q0", 50, 50, ("start",)), ("q1", 190, 50, ()), ("q2", 330, 50, ("acc",))]
NFA_EDGES = [dict(s="q0", d="q0", l="0, 1", ang=90), dict(s="q0", d="q1", l="0"), dict(s="q1", d="q2", l="1")]

DFA_STATES = [("{q0}", 60, 85, ("start",)), ("{q0,q1}", 220, 85, ()), ("{q0,q2}", 380, 85, ("acc",))]
DFA_EDGES = [dict(s="{q0}", d="{q0}", l="1", ang=90), dict(s="{q0}", d="{q0,q1}", l="0"),
             dict(s="{q0,q1}", d="{q0,q1}", l="0", ang=90), dict(s="{q0,q1}", d="{q0,q2}", l="1", bend=14),
             dict(s="{q0,q2}", d="{q0,q1}", l="0", bend=14), dict(s="{q0,q2}", d="{q0}", l="1", bend=52, lp=0.5)]

TABLE = [("→ {q0}", "{q0, q1}", "{q0}"), ("{q0, q1}", "{q0, q1}", "{q0, q2}"), ("* {q0, q2}", "{q0, q1}", "{q0}")]
