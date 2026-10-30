"""Sankey diagram of the green / orange / red screening of the quay walls.

Follows every wall in the municipal asset register through the decision tree
of the report (Figure 1.2):

  1. Past design life?   No  -> GREEN
  2. Masonry wall?       No  -> ORANGE
                         Yes -> calculate Pf; RED if Pf > Pf,target, else ORANGE

A wall is past its design life when `Eindjaar` (the register's theoretical end
year, Aanlegjaar + design life; 80 years for every walmuur) is before
REFERENCE_YEAR, the current year. It is masonry when `Bouwmateriaal` lists
Metselwerk. The report text of Section 1.4 still says 100 years and 2030; this
script uses the register's own term and the current year.

The last split, red against orange, is not drawn. There is no Pf per wall yet
and the team has not chosen Pf,target, so these walls end in one hatched node
"red or orange". Bands are coloured by the class a wall ends in.

Choices, all set as constants below:
  * band width is wall length (WEIGHT); register segments of a few metres
    would otherwise count as much as a 1 km bank protection,
  * only Status "In gebruik",
  * `Eindjaar` missing, or at or before `Aanlegjaar` (entry errors), ends in
    "not classified", because the tree has no rule for it,
  * an object with no material recorded counts as not masonry,
  * KM060028 has Aanlegjaar 2118, a year in the future, read as 2018,
  * a walmuur renewed on steel is screened from its renewal year
    (walmuur_foundation.csv, with_renewals), since the register keeps the
    year of the old wall. Only the walmuren have foundation data, so the
    register figure keeps the register years.

Writes two figures: the quay wall study population of the register (Muur,
Kademuur, Beschoeiing, Damwand) and the 51 walmuren of the Wervengebied that
the strength model computes.
Run: python scripts/plot_screening_sankey.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.colors import to_rgba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AREAAL = ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json"
FOUNDATION = ROOT / "data" / "processed" / "walmuur_foundation.csv"
FIGURES = ROOT / "figures"

REFERENCE_YEAR = 2026
STATUS = "In gebruik"
QUAY_TYPES = ["Muur", "Kademuur", "Beschoeiing", "Damwand"]
WEIGHT = "length"                    # band width: "length" (m) or "count" (objects)
YEAR_FIXES = {"KM060028": 2018}      # Aanlegjaar 2118 is a typo for 2018

CANALS = {"Oude Gracht": "Oudegracht", "Nieuwe Gracht": "Nieuwegracht",
          "Kromme Nieuwe Gracht": "Kromme Nieuwegracht"}
GROUP_NOTES = {"Beschoeiing": "bank protection", "Damwand": "sheet pile wall",
               "Kademuur": "quay wall, incl. 51 walmuren",
               "Muur": "werf- and kluismuren"}

# Colours: status palette (good / warning / critical, CVD checked). Orange is
# drawn amber, as in the report's flowchart.
GREEN = "#0ca30c"
ORANGE = "#fab219"
RED = "#d03b3b"
UNCLASSIFIED = "#c3c2b7"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
SURFACE = "#ffffff"

BAND_ALPHA = 0.38
NODE_W = 0.05                        # node width, in column spacings
GAP = 0.05                           # vertical gap between nodes, share of height

# Nodes of columns 1 to 3, top to bottom: (label, note, colour).
NODES = {
    "l:within": ("Within design life", f"Eindjaar {REFERENCE_YEAR} or later", INK_2),
    "l:past": ("Past design life", f"Eindjaar before {REFERENCE_YEAR}", INK_2),
    "l:unknown": ("No reliable end year", "missing, or before Aanlegjaar", INK_2),
    "m:other": ("Not masonry", "or no material recorded", INK_2),
    "m:masonry": ("Masonry", "Bouwmateriaal lists Metselwerk", INK_2),
    "c:green": ("Green", "regular maintenance", GREEN),
    "c:orange": ("Orange", "other model, further inspection", ORANGE),
    "c:pf": ("Red or orange", "Pf against Pf,target, not yet computed", "hatched"),
    "c:unclassified": ("Not classified", "no rule for a missing end year", UNCLASSIFIED),
}
CLASSES = ["green", "orange", "pf", "unclassified"]
HEADERS = ["1  Past design life?", "2  Masonry wall?", "3  Class"]


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str)
         .str.replace(",", ".", regex=False)
         .replace({"None": None, "": None}),
        errors="coerce",
    )


def load() -> pd.DataFrame:
    features = json.loads(AREAAL.read_text())["features"]
    df = pd.DataFrame([f.get("properties") or {} for f in features])
    for col in ("Aanlegjaar", "Eindjaar", "Lengte"):
        df[col] = to_num(df[col])
    for nummer, year in YEAR_FIXES.items():
        row = df["Nummer"] == nummer
        shift = year - df.loc[row, "Aanlegjaar"].iloc[0]
        print(f"Warning: {nummer} Aanlegjaar {year - shift:.0f} read as {year}")
        df.loc[row, ["Aanlegjaar", "Eindjaar"]] += shift
    return df


def classify(df: pd.DataFrame) -> pd.DataFrame:
    """Add the answers to the two questions and the resulting class."""
    end = df["Eindjaar"]
    known = end.notna() & ~(end <= df["Aanlegjaar"])
    past = known & (end < REFERENCE_YEAR)
    masonry = df["Bouwmateriaal"].fillna("").str.contains("Metselwerk")
    life = np.select([~known, past], ["unknown", "past"], "within")
    material = np.where(masonry, "masonry", "other")
    cls = np.select([life == "within", life == "unknown", masonry],
                    ["green", "unclassified", "pf"], "orange")
    return df.assign(life=life, material=material, cls=cls)


def register(df: pd.DataFrame) -> pd.DataFrame:
    """Quay wall study population, grouped by Objecttype."""
    q = df[df["Objecttype"].isin(QUAY_TYPES) & (df["Status"] == STATUS)]
    return classify(q.assign(group=q["Objecttype"]))


def walmuren(df: pd.DataFrame) -> pd.DataFrame:
    """The 51 named walmuren of the register, grouped by canal."""
    w = df[(df["Kunstwerktype Utrecht"] == "Walmuur")
           & (df["Naam"].fillna("").str.strip() != "")]
    canal = w["Naam"].str.extract(f"^({'|'.join(CANALS)})")[0].map(CANALS)
    w = classify(w.assign(group=canal))
    if w["group"].isna().any():
        raise SystemExit("Walmuren on an unknown canal: "
                         + ", ".join(w.loc[w["group"].isna(), "Naam"]))
    return w


def with_renewals(w: pd.DataFrame) -> pd.DataFrame:
    """The walmuren screened from the year their foundation was renewed.

    The register does not update `Aanlegjaar` after a wall is renewed on steel,
    so a renewed wall can look past its design life. For the walls with status
    "renewed" in walmuur_foundation.csv (build_walmuur_foundation.py), the
    design life runs from the renewal year instead; `Aanlegjaar` and
    `Eindjaar` themselves keep the register's values.
    """
    f = pd.read_csv(FOUNDATION)
    year = w["Nummer"].map(f[f["status"] == "renewed"].set_index("Nummer")["year"])
    shift = (year - w["Aanlegjaar"]).fillna(0)
    c = classify(w.assign(Aanlegjaar=w["Aanlegjaar"] + shift, Eindjaar=w["Eindjaar"] + shift))
    return w.assign(life=c["life"], cls=c["cls"], renewed=year)


def links(c: pd.DataFrame) -> pd.DataFrame:
    """One band per (source node, target node, final class)."""
    c = c.assign(len=c["Lengte"].fillna(0), g="g:" + c["group"],
                 l="l:" + c["life"], m="m:" + c["material"], k="c:" + c["cls"])
    past = c["life"] == "past"
    cols = ["src", "dst", "cls", "len"]
    hops = pd.concat([
        c[["g", "l", "cls", "len"]].set_axis(cols, axis=1),
        c.loc[past, ["l", "m", "cls", "len"]].set_axis(cols, axis=1),
        c.loc[past, ["m", "k", "cls", "len"]].set_axis(cols, axis=1),
        c.loc[~past, ["l", "k", "cls", "len"]].set_axis(cols, axis=1),
    ])
    out = hops.groupby(["src", "dst", "cls"], as_index=False).agg(
        length=("len", "sum"), n=("len", "size"))
    out["value"] = out["length"] if WEIGHT == "length" else out["n"]
    return out


def band(x0: float, y0: float, x1: float, y1: float, h: float) -> MplPath:
    """Band of height h from top-left (x0, y0) to top-right (x1, y1)."""
    xm = (x0 + x1) / 2
    verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 - h),
             (xm, y1 - h), (xm, y0 - h), (x0, y0 - h), (x0, y0)]
    C, L = MplPath.CURVE4, MplPath.LINETO
    return MplPath(verts, [MplPath.MOVETO, C, C, C, L, C, C, C, MplPath.CLOSEPOLY])


def style(cls: str, alpha: float) -> dict:
    """Fill (and hatch, for the undecided red-or-orange class) of a class."""
    if cls == "pf":
        return dict(facecolor=to_rgba(ORANGE, alpha), hatch="///",
                    hatchcolor=to_rgba(RED, min(1, 2 * alpha)))
    colour = {"green": GREEN, "orange": ORANGE, "unclassified": UNCLASSIFIED}[cls]
    return dict(facecolor=to_rgba(colour, alpha))


def label(ax, x: float, y: float, ha: str, name: str, stats: str, note: str) -> None:
    """Three-line node label: name, size, note. White halo over the bands."""
    halo = [patheffects.withStroke(linewidth=3, foreground=SURFACE)]
    dx = -6 if ha == "right" else 6
    for text, dy, va, kw in [
        (name, 2, "bottom", dict(fontsize=9.5, fontweight="bold", color=INK)),
        (stats, -1, "top", dict(fontsize=8.5, color=INK_2)),
        (note, -12.5, "top", dict(fontsize=7.5, color=MUTED)),
    ]:
        ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va=va, path_effects=halo, **kw)


def plot(c: pd.DataFrame, title: str, subtitle: str, group_header: str, fmt,
         notes: dict, out: Path) -> None:
    lk = links(c)
    # Groups top to bottom by where their flow ends (mean class rank), which
    # keeps the bands from crossing more than they need to.
    first = lk[lk["src"].str.startswith("g:")]
    rank = first["cls"].map(CLASSES.index) * first["value"]
    rank = rank.groupby(first["src"]).sum() / first.groupby("src")["value"].sum()
    groups = list(rank.sort_values().index)
    order = {k: i for i, k in enumerate(groups + list(NODES))}
    keys = sorted(set(lk["src"]) | set(lk["dst"]), key=lambda k: order[k])
    column = {k: "glmc".index(k[0]) for k in keys}

    def node_total(field: str) -> dict:
        into = lk.groupby("dst")[field].sum()
        out_of = lk.groupby("src")[field].sum()
        return {k: max(into.get(k, 0), out_of.get(k, 0)) for k in keys}

    value, length, count = node_total("value"), node_total("length"), node_total("n")
    columns = [[k for k in keys if column[k] == i] for i in range(4)]
    scale = (1 - GAP * (max(map(len, columns)) - 1)) / max(
        sum(value[k] for k in ks) for ks in columns)

    # Stack each column downwards. A column that carries only part of the
    # flow (the material question) starts level with the node feeding it.
    top: dict[str, float] = {}
    for ks in columns:
        sources = lk.loc[lk["dst"] == ks[0], "src"]
        y = max((top[s] for s in sources), default=1.0)
        for k in ks:
            top[k] = y
            y -= value[k] * scale + GAP

    fig, ax = plt.subplots(figsize=(11, 6.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_axis_off()

    lk = lk.assign(so=lk["src"].map(order), do=lk["dst"].map(order),
                   co=lk["cls"].map(CLASSES.index), h=lk["value"] * scale)
    y_out, y_in = dict(top), dict(top)
    lk["y0"] = 0.0
    for i, r in lk.sort_values(["so", "do", "co"]).iterrows():
        lk.at[i, "y0"] = y_out[r["src"]]
        y_out[r["src"]] -= r["h"]
    lk["y1"] = 0.0
    for i, r in lk.sort_values(["do", "so", "co"]).iterrows():
        lk.at[i, "y1"] = y_in[r["dst"]]
        y_in[r["dst"]] -= r["h"]

    for r in lk.itertuples():
        path = band(column[r.src] + NODE_W, r.y0, column[r.dst], r.y1, r.h)
        ax.add_patch(PathPatch(path, edgecolor=SURFACE, linewidth=0.6,
                               **style(r.cls, BAND_ALPHA)))

    for k in keys:
        x, h = column[k], value[k] * scale
        name, note, colour = NODES.get(k, (k[2:], notes.get(k[2:], ""), INK_2))
        fill = style("pf", 1.0) if colour == "hatched" else dict(facecolor=colour)
        ax.add_patch(Rectangle((x, top[k] - h), NODE_W, h, linewidth=0,
                               edgecolor="none", **fill))
        first = column[k] == 0
        label(ax, x if first else x + NODE_W, top[k] - h / 2,
              "right" if first else "left", name, fmt(length[k], count[k]), note)

    header = dict(fontsize=9.5, fontweight="bold", color=INK_2, va="bottom")
    ax.text(NODE_W, 1.07, group_header, ha="right", **header)
    for i, text in enumerate(HEADERS, start=1):
        ax.text(i, 1.07, text, ha="left", **header)
    ax.set_xlim(-0.95, 4.35)
    ax.set_ylim(-0.02, 1.12)

    fig.text(0.03, 0.965, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.03, 0.915, subtitle, fontsize=8.5, color=INK_2, va="top",
             linespacing=1.5)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.82, bottom=0.02)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def summary(c: pd.DataFrame) -> str:
    s = c.groupby("cls").agg(objects=("cls", "size"), length_m=("Lengte", "sum"))
    s = s.reindex([k for k in CLASSES if k in s.index])
    s.loc["total"] = s.sum()
    s["share_length"] = (s["length_m"] / s.loc["total", "length_m"]).map("{:.0%}".format)
    s["length_m"] = s["length_m"].round()
    return s.astype({"objects": int}).to_string()


def main() -> None:
    df = load()
    w = with_renewals(walmuren(df))
    width = "length" if WEIGHT == "length" else "number of objects"
    populations = {
        "register": (
            register(df),
            "Quay walls through the green / orange / red screening",
            f"Municipality of Utrecht asset register, quay wall study population "
            f"(Muur, Kademuur, Beschoeiing, Damwand), status {STATUS}.\n"
            f"Band width is {width}. Bands are coloured by the class each wall "
            f"ends in; red and orange are split once Pf per wall is known.",
            "Objecttype",
            lambda m, n: f"{m / 1000:.1f} km  ·  {n:,} objects",
            GROUP_NOTES,
        ),
        "walmuren": (
            w,
            "Walmuren of the Wervengebied through the screening",
            "The 51 named walmuren of the asset register (Kunstwerktype Walmuur); the "
            f"{w['renewed'].notna().sum()} renewed on steel count from their renewal year.\n"
            f"Band width is {width}. All {(w['life'] == 'past').sum()} walls past design "
            "life are masonry, so none is orange on material alone.",
            "Canal",
            lambda m, n: f"{m:,.0f} m  ·  {n} walls",
            {},
        ),
    }
    for key, (c, title, subtitle, group_header, fmt, notes) in populations.items():
        out = FIGURES / f"screening_sankey_{key}.png"
        plot(c, title, subtitle, group_header, fmt, notes, out)
        print(f"{title}\n  -> {out.relative_to(ROOT)}")
        print(summary(c))
        print()


if __name__ == "__main__":
    main()
