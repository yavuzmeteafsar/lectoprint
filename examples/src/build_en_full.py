import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "lectoprint", "scripts"))
import doc_builder as db
import bank
import figs
import practice

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "Lectoprint_EN_Full_Notes.pdf")
d = db.Doc(OUT, "Lectoprint sample · Finite Automata: NFA → DFA · Full notes (EN)", "Finite Automata: NFA to DFA", "Lectoprint", lang="en")
d.cover(["Finite Automata", "NFA → DFA"], "Full lecture notes with exam practice",
        ["Mode: English (default)", "Content: full notes + 12 / 10 / 6 / 10 questions", "Source: original sample notes written for this example"], "LECTOPRINT")
d.toc([("1", "Deterministic Finite Automata"), ("2", "Nondeterministic Finite Automata"), ("3", "Subset Construction"),
       ("4", "ε-NFAs and ε-closure"), ("5", "Glossary"), ("6", "Exam Practice"), ("7", "Key Exam Points")])

d.sec_hdr("1", "Deterministic Finite Automata")
d.h2("1.1 What and why")
d.body("A finite automaton is the simplest model of a machine with memory: it has a fixed, finite number of states and reads its input one symbol at a time. "
       "<b>Deterministic</b> means there is never a choice: from each state, each symbol leads to exactly one next state. "
       "This makes a DFA easy to run in hardware or code, and it is the reference model the rest of the chapter is compared against.")
d.src_box("A DFA is a 5-tuple (Q, Σ, δ, q<sub>0</sub>, F) where Q is a finite set of states, Σ is the input alphabet, δ : Q × Σ → Q is the transition function, q<sub>0</sub> ∈ Q is the start state and F ⊆ Q is the set of accepting states.",
          src=bank.ref("en", 1))
d.def_tbl([("Q", "Finite set of states."), ("Σ", "Input alphabet: a finite, non-empty set of symbols."),
           ("δ", "Total function Q × Σ → Q; exactly one next state per (state, symbol)."),
           ("q<sub>0</sub>", "The single start state."), ("F", "Accepting states; may be empty.")])
d.body("A DFA accepts a string w when the run that starts in q<sub>0</sub> and follows w ends in F. Using the extended transition function:")
d.math([r"\hat\delta(q,\varepsilon)=q,\qquad \hat\delta(q,wa)=\delta(\hat\delta(q,w),a)", r"w\in L(A)\Leftrightarrow \hat\delta(q_0,w)\in F"])
d.warn_box("If F = ∅ the DFA accepts nothing, not even the empty string ε. A DFA with no accepting states recognises the empty language ∅.")

d.sec_hdr("2", "Nondeterministic Finite Automata")
d.h2("2.1 What and why")
d.body("Many languages are easier to describe by <i>guessing</i>. For \"strings that end in 01\" it is natural to say: wait, and at some point guess that the final 01 starts here. "
       "An NFA allows exactly this: from one state, a symbol may lead to several states, or to none. The NFA accepts if <b>at least one</b> of its possible runs ends in an accepting state.")
d.src_box("An NFA is a 5-tuple (Q, Σ, δ, q<sub>0</sub>, F) defined like a DFA, except that δ : Q × Σ → P(Q). The NFA accepts w if at least one run on w ends in a state of F.",
          src=bank.ref("en", 2))
d.h2("2.2 Example: strings that end in 01")
d.q_box("Example 1 (source, p.2)", "Build an NFA over Σ = {0, 1} that accepts exactly the strings ending in 01.")
d.diagram(390, 105, figs.NFA_STATES, figs.NFA_EDGES, "NFA N for strings ending in 01 (redrawn, p.2)")
d.body("q<sub>0</sub> reads any prefix. On a 0 it may also <i>guess</i> that this 0 is the second-to-last symbol and move to q<sub>1</sub>; a following 1 reaches the accepting state q<sub>2</sub>. "
       "If the guess was wrong, that run simply dies: q<sub>1</sub> has no move on 0 and q<sub>2</sub> has no moves at all.")
d.tip_box("When designing an NFA for \"ends in …\", keep a self-loop on the start state and spell out the suffix as a chain of states. The loop absorbs the prefix; nondeterminism picks where the suffix starts.")

d.sec_hdr("3", "Subset Construction")
d.h2("3.1 What and why")
d.body("NFAs are convenient, but a machine cannot run on guesses. The subset construction removes the guessing: the DFA keeps track of <b>every state the NFA could currently be in</b>. "
       "A DFA state is therefore a set of NFA states, and its next state is the set of all places those states can move to.")
d.src_box("Given an NFA N = (Q<sub>N</sub>, Σ, δ<sub>N</sub>, q<sub>0</sub>, F<sub>N</sub>), the subset construction builds a DFA D whose states are subsets of Q<sub>N</sub>, with start state {q<sub>0</sub>}, transitions δ<sub>D</sub>(S, a) = ∪<sub>p∈S</sub> δ<sub>N</sub>(p, a), and accepting states all S with S ∩ F<sub>N</sub> ≠ ∅.",
          src=bank.ref("en", 3))
d.math([r"\delta_D(S,a)=\bigcup_{p\in S}\delta_N(p,a)", r"F_D=\{\,S\subseteq Q_N : S\cap F_N\neq\emptyset\,\}", r"|Q_D|\leq 2^{|Q_N|}"])
d.h2("3.2 Example: converting N")
d.q_box("Example 2 (source, p.3)", "Convert the NFA N of Example 1 to a DFA using the subset construction. Build only the reachable states.")
d.diagram(390, 105, figs.NFA_STATES, figs.NFA_EDGES, "NFA N again, for reference (redrawn, p.2)")
d.h3("Step 1: start state")
d.formula(["start = {q0}"])
d.h3("Step 2: moves from {q0}")
d.formula(["δD({q0}, 0) = δN(q0, 0) = {q0, q1}    new", "δD({q0}, 1) = δN(q0, 1) = {q0}"])
d.h3("Step 3: moves from {q0, q1}")
d.formula(["δD({q0,q1}, 0) = {q0, q1} ∪ ∅ = {q0, q1}", "δD({q0,q1}, 1) = {q0} ∪ {q2} = {q0, q2}    new"])
d.h3("Step 4: moves from {q0, q2}")
d.formula(["δD({q0,q2}, 0) = {q0, q1} ∪ ∅ = {q0, q1}", "δD({q0,q2}, 1) = {q0} ∪ ∅ = {q0}"])
d.body("No new sets appeared in Step 4, so the construction stops with three states.")
d.h3("Step 5: accepting states and table")
d.body("Only {q<sub>0</sub>, q<sub>2</sub>} contains the NFA accepting state q<sub>2</sub>, so it is the only accepting DFA state. → marks the start state, * an accepting state.")
d.grid(["DFA state", "0", "1"], figs.TABLE, widths=[2, 2, 2], green_rows=(2,), caption="Transition table of D (green: accepting)")
d.diagram(440, 150, figs.DFA_STATES, figs.DFA_EDGES, "DFA D produced by the subset construction")
d.info_box("Check", "A script ran D and the original definition (\"ends in 01\") on every binary string up to length 8; they agree on all of them.")
d.warn_box("2<super>3</super> = 8 is only the upper bound. Sets such as {q<sub>1</sub>} or ∅ are never reached here, so they are not states of D. Listing them is a common exam mistake.")

d.sec_hdr("4", "ε-NFAs and ε-closure")
d.h2("4.1 What and why")
d.body("Some constructions are simpler if the automaton may also move <b>without reading a symbol</b>. These ε-moves add no power, but the subset construction must account for them by closing every set under ε-moves.")
d.src_box("ε-closure(q) is the set of states reachable from q by zero or more ε-transitions. For an ε-NFA the subset construction starts with ε-closure(q<sub>0</sub>) and uses δ<sub>D</sub>(S, a) = ε-closure(∪<sub>p∈S</sub> δ<sub>N</sub>(p, a)).",
          src=bank.ref("en", 4))
d.tip_box("ε-closure(q) always contains q, because zero moves are allowed.")

practice.glossary(d, "5", "en", db.PRIMARY)
practice.practice(d, "6", "en", (12, 10, 6, 10), db.PRIMARY)
practice.summary(d, "7", "en", db.SUMMARY)
d.build()
print(OUT)
