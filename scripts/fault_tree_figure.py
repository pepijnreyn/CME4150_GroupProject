"""TikZ drawing of the fault tree of report section 3.1 (Figure 3.1).

The tree is drawn left to right: the top event on the left, the basic events in
one column on the right. Gates are labelled OR or AND. The repair chain
("weakening not repaired in time") feeds both resistance branches and is drawn
once; WT and GW appear twice as the same event. The logic matches fault_tree.py:

  not_recognised = (S1 or S2 or S3 or I1 or I2) and NW
  not_repaired   = not_recognised or I3 or (L1 or L2 or L3 or L4)

Writes report/figures/fault_tree_tikz.tex. Run: python3 scripts/fault_tree_figure.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures" / "fault_tree_tikz.tex"

# category: T technical, H human, O organisational, E external (colours of the old figure)
LEAVES = {
    "G1": ("T", "Soil heavier or pushes harder"), "G2": ("T", "Canal bed lower than assumed"),
    "W2": ("T", "Drainage blocked behind the wall"), "GW": ("E", "Groundwater outside normal range"),
    "Q1": ("O", "Traffic heavier than allowed"), "Q2": ("T", "Vehicles, terraces or goods at the edge"),
    "Q3": ("O", "Crane or construction traffic"), "E1": ("E", "Vessel impact or mooring overload"),
    "E2": ("T", "Root pressure from trees"), "E3": ("T", "Larger scour event"),
    "E4": ("E", "Excavation or pipe burst"), "P1": ("T", "Bacteria thin the piles"),
    "P3": ("T", "Pile condition worse than assumed"), "WT": ("T", "Wall is the weaker type 1"),
    "M1": ("T", "Masonry degrades"), "M2": ("T", "Cross-section differs from drawing"),
    "S1": ("H", "Wrong year or foundation in register"), "S2": ("O", "Screening rule misses the wall"),
    "S3": ("O", "Model misses the risk"), "I1": ("O", "Targeted inspection not done in time"),
    "I2": ("H", "Damage under water missed"), "NW": ("T", "No visible warning before failure"),
    "I3": ("H", "Warning not acted on"), "L1": ("O", "Capacity or budget too small"),
    "L2": ("O", "Heritage permit delays repair"), "L3": ("O", "Cellar owner consents late"),
    "L4": ("E", "Unexpected condition delays repair"),
}
# (label, gate, children); a str child is a basic event, "REPAIR" the shared chain
REPAIR = ("Weakening not repaired in time", "OR", [
    ("Weakness not recognised", "AND", [
        ("Screening or targeted inspection misses it", "OR", ["S1", "S2", "S3", "I1", "I2"]),
        "NW"]),
    "I3",
    ("Repair comes too late", "OR", ["L1", "L2", "L3", "L4"])])
TREE = ("Programme does not prevent a wall failure before renewal", "OR", [
    ("Load too high", "OR", [
        ("Soil load", "OR", ["G1", "G2"]),
        ("Water load", "OR", ["W2", "GW"]),
        ("Surcharge", "OR", ["Q1", "Q2", "Q3"]),
        ("Sudden impact, scour or works", "OR", ["E1", "E2", "E3", "E4"])]),
    ("Resistance too low", "OR", [
        ("Piles fail in bending", "AND", [("Piles weak", "OR", ["P1", "P3", "WT", "GW"]), "REPAIR"]),
        ("Wall overturns", "AND", [("Wall weak", "OR", ["M1", "M2", "WT"]), "REPAIR"])])])

COL = 1.85        # cm between levels
ROW = 0.37        # cm between basic events
BOX_W = 1.3       # cm, width of a gate label
LEAF_X = 6 * COL


def emit():
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
             r"minimum height=0.3cm},line/.style={ftL,line width=0.4pt}}"]
    row = [0]
    repair_y = {}

    def leaf(code):
        y = -row[0] * ROW
        row[0] += 1
        cat, text = LEAVES[code]
        lines.append(rf"\node[draw=ft{cat}b,fill=ft{cat},rounded corners=1pt,anchor=west,"
                     rf"minimum height=0.3cm,text width=4.35cm] at ({LEAF_X:.2f},{y:.2f}) "
                     rf"{{\textbf{{\color{{ft{cat}b}}{code}}}\ \ {text}}};")
        return y

    def node(item, level):
        if isinstance(item, str):
            if item == "REPAIR":
                if "y" in repair_y:      # drawn once; the second branch refers to it
                    y = -row[0] * ROW
                    row[0] += 1
                    lines.append(rf"\node[ev,anchor=west,dashed,text width=2.9cm] at ({level * COL:.2f},{y:.2f})"
                                 rf" {{\itshape Weakening not repaired in time (as above)}};")
                    return y, False
                y = node(REPAIR, level)[0]
                repair_y["y"] = y
                return y, False
            return leaf(item), False
        label, gate, children = item
        ys = [(node(c, level + 1), c) for c in children]
        y = sum(v[0][0] for v in ys) / len(ys) if len(ys) > 1 else ys[0][0][0]
        x = level * COL
        lines.append(rf"\node[ev,anchor=west] at ({x:.2f},{y:.2f}) {{{label}}};")
        gx = x + BOX_W + 0.06
        lines.append(rf"\node[{'andgate' if gate == 'AND' else 'gate'},anchor=west] (g) at ({gx:.2f},{y:.2f}) {{{gate}}};")
        bus = gx + 0.52
        lines.append(rf"\draw[line] (g.east) -- ({bus:.2f},{y:.2f});")
        cy = [v[0][0] for v in ys]
        lines.append(rf"\draw[line] ({bus:.2f},{min(cy):.2f}) -- ({bus:.2f},{max(cy):.2f});")
        for (cyy, _), child in ys:
            target = LEAF_X if isinstance(child, str) and child != "REPAIR" else (level + 1) * COL
            lines.append(rf"\draw[line] ({bus:.2f},{cyy:.2f}) -- ({target:.2f},{cyy:.2f});")
        return y, False

    top = node(TREE, 0)[0]
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def main() -> None:
    OUT.write_text("% Generated by scripts/fault_tree_figure.py.\n"
                   + emit() + "\n")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
