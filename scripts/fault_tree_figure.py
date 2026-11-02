"""TikZ drawing of the fault tree of report section 3.1 (Figure 3.1), as it is computed.

The tree is drawn left to right: the top event on the left, the basic events in
one column on the right. Gates are labelled OR or AND. Every event and gate
carries its probability for the median wall (fault_tree.py, load events scaled
to its years until renewal). The logic is that of fault_tree.py:

  top            = load OR (LS AND not_repaired)
  not_recognised = (S1 or S2 or S3 or I1 or I2) and NW
  not_repaired   = not_recognised or I3 or (L1 or L2 or L3 or L4)

LS, a limit state of the failure model before renewal, holds the eight causes
that the model of report section 2.1 contains (soil, canal bed, groundwater,
pile decay and condition, wall type, masonry, cross-section). They are listed
inside its box rather than drawn as separate events, so nothing counts twice.

Writes figures/fault_tree_tikz.tex. Run: python3 scripts/fault_tree_figure.py
"""

from pathlib import Path

import fault_tree as FT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "fault_tree_tikz.tex"

# category: T technical, H human, O organisational, E external (colours of the old figure)
LEAVES = {
    "W2": ("T", "Drainage blocked behind the wall"),
    "Q1": ("O", "Traffic heavier than allowed"), "Q2": ("T", "Vehicles, terraces or goods at the edge"),
    "Q3": ("O", "Crane or construction traffic"), "E1": ("E", "Vessel impact or mooring overload"),
    "E2": ("T", "Root pressure from trees"), "E3": ("T", "Larger scour event"),
    "E4": ("E", "Excavation or pipe burst"),
    "S1": ("H", "Wrong year or foundation in register"), "S2": ("O", "Screening rule misses the wall"),
    "S3": ("O", "Model misses the risk"), "I1": ("O", "Targeted inspection not done in time"),
    "I2": ("H", "Damage under water missed"), "NW": ("T", "No visible warning before failure"),
    "I3": ("H", "Warning not acted on"), "L1": ("O", "Capacity or budget too small"),
    "L2": ("O", "Heritage permit delays repair"), "L3": ("O", "Cellar owner consents late"),
    "L4": ("E", "Unexpected condition delays repair"),
}
# The causes inside the model event LS (report section 2.1)
LS_PARTS = [("G1", "T", "soil load"), ("G2", "T", "canal bed"), ("GW", "E", "groundwater"),
            ("P1", "T", "pile decay"), ("P3", "T", "pile condition"), ("WT", "T", "wall type~1"),
            ("M1", "T", "masonry"), ("M2", "T", "cross-section")]
LS_ROWS = 5
# (label, gate, children); a str child is a basic event
REPAIR = ("Weakening not repaired in time", "OR", [
    ("Weakness not recognised", "AND", [
        ("Screening or targeted inspection misses it", "OR", ["S1", "S2", "S3", "I1", "I2"]),
        "NW"]),
    "I3",
    ("Repair comes too late", "OR", ["L1", "L2", "L3", "L4"])])
TREE = ("Programme does not prevent a wall failure before renewal", "OR", [
    ("Load event beyond the model", "OR", [
        "W2",
        ("Surcharge beyond the model", "OR", ["Q1", "Q2", "Q3"]),
        ("Sudden impact, scour or works", "OR", ["E1", "E2", "E3", "E4"])]),
    ("Limit state reached, not repaired in time", "AND", ["LS", REPAIR])])

COL = 1.85        # cm between levels
ROW = 0.37        # cm between basic events
BOX_W = 1.3       # cm, width of a gate label
LEAF_X = 5 * COL
LEAF_W = 4.6      # cm, text width of a basic event; its probability stands to the right


def probabilities():
    """Probability of every basic event for the median wall, as fault_tree.py uses it."""
    T, M, _ = FT.read_walls()[FT.MEDIAN_WALL]
    p = FT.events("base", T, M)
    p["NW"], p["LS"] = p.pop("D"), p.pop("M")
    return p, T


def prob(item, p):
    if isinstance(item, str):
        return float(p[item])
    _, gate, children = item
    ps = [prob(c, p) for c in children]
    if gate == "AND":
        out = 1.0
        for x in ps:
            out *= x
        return out
    out = 1.0
    for x in ps:
        out *= 1 - x
    return 1 - out


def fmt(p):
    return "0" if p == 0 else f"{p:.2f}" if p >= 0.1 else f"{p:.3f}" if p >= 0.01 else f"{p:.4f}"


def emit(p):
    lines = [r"\definecolor{ftT}{HTML}{E3EDFA}\definecolor{ftTb}{HTML}{2A78D6}",
             r"\definecolor{ftH}{HTML}{FDEBD9}\definecolor{ftHb}{HTML}{C26A14}",
             r"\definecolor{ftO}{HTML}{EFE6F6}\definecolor{ftOb}{HTML}{7C3AED}",
             r"\definecolor{ftE}{HTML}{E6F2E0}\definecolor{ftEb}{HTML}{3F7D2A}",
             r"\definecolor{ftG}{HTML}{1F2937}\definecolor{ftL}{HTML}{6B7280}",
             r"\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{6.2}{7}\selectfont,"
             r"every node/.style={inner sep=1pt}]",
             r"\tikzset{gate/.style={draw=ftG,fill=white,rounded corners=1.5pt,"
             r"font=\fontsize{5}{5}\selectfont\bfseries,minimum width=0.42cm,minimum height=0.22cm},"
             r"andgate/.style={gate,fill=ftG,text=white},"
             r"ev/.style={draw=ftG,fill=white,rounded corners=1pt,align=left,text width=1.2cm,"
             r"minimum height=0.3cm},line/.style={ftL,line width=0.4pt},"
             r"pv/.style={font=\fontsize{5.6}{6}\selectfont\bfseries,text=ftG}}"]
    row = [0]

    def value(y, v):
        lines.append(rf"\node[pv,anchor=west] at ({LEAF_X + LEAF_W + 0.12:.2f},{y:.2f}) {{{fmt(v)}}};")

    def leaf(code):
        if code == "LS":
            y = -(row[0] + (LS_ROWS - 1) / 2) * ROW
            row[0] += LS_ROWS
            parts = ", ".join(rf"\textbf{{\color{{ft{c}b}}{k}}} {t}" for k, c, t in LS_PARTS)
            lines.append(rf"\node[draw=ftTb,fill=ftT,dashed,rounded corners=1pt,anchor=west,align=left,"
                         rf"text width={LEAF_W}cm] at ({LEAF_X:.2f},{y:.2f}) "
                         rf"{{\textbf{{\color{{ftTb}}LS}}\ \ Limit state in the model (Section~\ref{{sec:prob}})\\[1pt]"
                         rf"{{\fontsize{{5.6}}{{6.6}}\selectfont Piles break or wall overturns; contains {parts}}}}};")
            value(y, p["LS"])
            return y
        y = -row[0] * ROW
        row[0] += 1
        cat, text = LEAVES[code]
        lines.append(rf"\node[draw=ft{cat}b,fill=ft{cat},rounded corners=1pt,anchor=west,"
                     rf"minimum height=0.3cm,text width={LEAF_W}cm] at ({LEAF_X:.2f},{y:.2f}) "
                     rf"{{\textbf{{\color{{ft{cat}b}}{code}}}\ \ {text}}};")
        value(y, p[code])
        return y

    def node(item, level):
        if isinstance(item, str):
            return leaf(item)
        label, gate, children = item
        ys = [(node(c, level + 1), c) for c in children]
        y = sum(v[0] for v in ys) / len(ys)
        x = level * COL
        lines.append(rf"\node[ev,anchor=west] at ({x:.2f},{y:.2f}) {{{label}}};")
        gx = x + BOX_W + 0.06
        lines.append(rf"\node[{'andgate' if gate == 'AND' else 'gate'},anchor=west] (g) at ({gx:.2f},{y:.2f}) {{{gate}}};")
        lines.append(rf"\node[pv,anchor=north] at (g.south) {{{fmt(prob(item, p))}}};")
        bus = gx + 0.52
        lines.append(rf"\draw[line] (g.east) -- ({bus:.2f},{y:.2f});")
        cy = [v[0] for v in ys]
        lines.append(rf"\draw[line] ({bus:.2f},{min(cy):.2f}) -- ({bus:.2f},{max(cy):.2f});")
        for cyy, child in ys:
            target = LEAF_X if isinstance(child, str) else (level + 1) * COL
            lines.append(rf"\draw[line] ({bus:.2f},{cyy:.2f}) -- ({target:.2f},{cyy:.2f});")
        return y

    node(TREE, 0)
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def main() -> None:
    p, T = probabilities()
    top = prob(TREE, p)
    check = FT.tree({**p, "D": p["NW"], "M": p["LS"]})[0]
    assert abs(top - check) < 1e-12, (top, check)
    OUT.write_text("% Generated by scripts/fault_tree_figure.py.\n" + emit(p) + "\n")
    print(f"top event {top:.4f} (fault_tree.py {check:.4f}), {T:.2f} years until renewal"
          f" -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
