"""Histogram of design-life end year (`Eindjaar`) per building material.

Answers: are some materials more often past their design life than others?

One row per material, sorted by the share past design life. The left panel is
the distribution of `Eindjaar` (share of that material's objects per decade),
split into past and not yet past at REFERENCE_YEAR. The right panel is the
share past as a single number, so rows can be compared directly.

Read the result with the caveat from docs/output_areaal_overview.md:
`Eindjaar` is `Aanlegjaar` plus a standard term, and that term is set per
material (Hout mostly 25 yr, Staal 60, Beton and Metselwerk 80). A material
scores high either because its stock is old or because it was given a short
term. The row labels print the usual term so that stays visible.

Choices, all set as constants below:
  * only Status "In gebruik",
  * rows with `Eindjaar` at or before `Aanlegjaar` are dropped (entry errors),
  * an object listing several materials ("Hout, Staal") counts once under
    each of them,
  * materials with fewer than MIN_N dated objects are left out.

Writes two figures, one for every in-use object and one for the quay wall
study population (Muur, Kademuur, Beschoeiing, Damwand).
Run: python scripts/plot_design_life_by_material.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AREAAL = ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json"
FIGURES = ROOT / "figures"

REFERENCE_YEAR = 2026
STATUS = "In gebruik"
MIN_N = 20
QUAY_TYPES = ["Muur", "Kademuur", "Beschoeiing", "Damwand"]

# Decade bins from 1900 to 2130; everything earlier goes in one overflow
# bar drawn at OVERFLOW_X, set apart from the 1900 bin.
FIRST_DECADE, LAST_DECADE = 1900, 2130
OVERFLOW_X = 1880

# Colours: slots 1 and 2 of the reference categorical palette (CVD checked).
PAST = "#eb6834"
WITHIN = "#2a78d6"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#ffffff"


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
    df["Aanlegjaar"] = to_num(df["Aanlegjaar"])
    df["Eindjaar"] = to_num(df["Eindjaar"])
    return df


def by_material(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (object, material), dated and in use."""
    df = df[df["Status"] == STATUS]
    df = df[df["Eindjaar"].notna() & (df["Eindjaar"] > df["Aanlegjaar"])]
    df = df.assign(Materiaal=df["Bouwmateriaal"].fillna("").str.split(","))
    df = df.explode("Materiaal").reset_index(drop=True)
    df["Materiaal"] = df["Materiaal"].str.strip()
    df = df[df["Materiaal"] != ""]
    df["past"] = df["Eindjaar"] < REFERENCE_YEAR
    df["term"] = df["Eindjaar"] - df["Aanlegjaar"]
    return df


def summarise(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, g in m.groupby("Materiaal"):
        terms = g["term"].value_counts(normalize=True)
        rows.append({
            "Materiaal": name,
            "n": len(g),
            "past": int(g["past"].sum()),
            "share_past": g["past"].mean(),
            "term": int(terms.index[0]),
            "term_share": terms.iloc[0],
        })
    s = pd.DataFrame(rows)
    s = s[s["n"] >= MIN_N]
    return s.sort_values("share_past", ascending=False).reset_index(drop=True)


def decade_shares(years: pd.Series, past: pd.Series, n: int):
    """Share of n per decade bin, split into past / not past, plus overflow."""
    edges = np.arange(FIRST_DECADE, LAST_DECADE + 10, 10)
    clipped = years.clip(upper=LAST_DECADE - 1)
    in_range = clipped >= FIRST_DECADE
    past_counts, _ = np.histogram(clipped[in_range & past], edges)
    within_counts, _ = np.histogram(clipped[in_range & ~past], edges)
    overflow = (~in_range & past).sum(), (~in_range & ~past).sum()
    return edges, past_counts / n, within_counts / n, (overflow[0] / n, overflow[1] / n)


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def plot(m: pd.DataFrame, population: str, out: Path) -> pd.DataFrame:
    s = summarise(m)
    n_rows = len(s)
    height = 1.15 * n_rows + 2.1
    fig, axes = plt.subplots(
        n_rows, 2, figsize=(11, height),
        gridspec_kw={"width_ratios": [3.4, 1], "wspace": 0.08, "hspace": 0.62},
        sharex="col", sharey="col", squeeze=False,
    )
    fig.patch.set_facecolor(SURFACE)

    def y_at(inches_from_top: float) -> float:
        return 1 - inches_from_top / height

    y_max = 0
    for i, row in s.iterrows():
        g = m[m["Materiaal"] == row["Materiaal"]]
        edges, past, within, (o_past, o_within) = decade_shares(
            g["Eindjaar"], g["past"], row["n"])
        y_max = max(y_max, (past + within).max(), o_past + o_within)

        ax = axes[i, 0]
        style(ax)
        bar = dict(width=10, align="edge", edgecolor=SURFACE, linewidth=1)
        ax.bar(edges[:-1], past, color=PAST, **bar)
        ax.bar(edges[:-1], within, bottom=past, color=WITHIN, **bar)
        ax.bar(OVERFLOW_X, o_past, color=PAST, **bar)
        ax.bar(OVERFLOW_X, o_within, bottom=o_past, color=WITHIN, **bar)
        ax.axvline(REFERENCE_YEAR, color=INK_2, linewidth=1, linestyle=(0, (3, 2)))
        name = ax.text(0.0, 1.06, row["Materiaal"], transform=ax.transAxes,
                       fontsize=10, fontweight="bold", color=INK, va="bottom")
        ax.annotate(f"{row['n']:,} objects  ·  {row['term']}-yr design life "
                    f"for {row['term_share']:.0%}",
                    xy=(1, 0), xycoords=name, xytext=(8, 0),
                    textcoords="offset points", fontsize=8.5, color=INK_2,
                    va="bottom")

        ax = axes[i, 1]
        style(ax)
        ax.grid(False)
        ax.barh(0, 1, height=0.55, color=GRID)
        ax.barh(0, row["share_past"], height=0.55, color=PAST)
        ax.text(1.04, 0, f"{row['share_past']:.0%}", va="center", ha="left",
                fontsize=10, fontweight="bold", color=INK)
        ax.set_yticks([])
        ax.spines["bottom"].set_visible(False)

    hist = axes[-1, 0]
    hist.set_ylim(0, y_max * 1.1)
    hist.yaxis.set_major_locator(MaxNLocator(nbins=2))
    hist.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    hist.set_xlim(OVERFLOW_X - 6, LAST_DECADE + 2)
    ticks = [OVERFLOW_X + 5, 1900, 1950, 2000, 2050, 2100]
    hist.set_xticks(ticks, ["< 1900", "1900", "1950", "2000", "2050", "2100"])
    hist.set_xlabel("End of design life (Eindjaar), per decade",
                    fontsize=9, color=INK_2, labelpad=6)
    axes[0, 0].text(REFERENCE_YEAR + 2, 1.0, str(REFERENCE_YEAR),
                    transform=axes[0, 0].get_xaxis_transform(),
                    fontsize=8, color=INK_2, va="top")

    bars = axes[-1, 1]
    bars.set_xlim(0, 1.25)
    bars.set_xticks([])
    bars.set_ylim(-0.6, 0.6)
    axes[0, 1].text(0, 1.06, f"Past design life in {REFERENCE_YEAR}",
                    transform=axes[0, 1].transAxes, fontsize=10,
                    fontweight="bold", color=INK, va="bottom")

    left = 0.075
    fig.text(left, y_at(0.22), "Share past design life by material",
             fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(left, y_at(0.52),
             f"{population}.\nLeft: share of each material's objects per decade "
             "of Eindjaar. Objects with several materials count once per material.",
             fontsize=8.5, color=INK_2, va="top", linespacing=1.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=PAST),
               plt.Rectangle((0, 0), 1, 1, color=WITHIN)]
    fig.legend(handles, [f"Eindjaar before {REFERENCE_YEAR} (past design life)",
                         f"Eindjaar {REFERENCE_YEAR} or later"],
               loc="upper left", bbox_to_anchor=(left - 0.008, y_at(0.95)),
               ncol=2, frameon=False, fontsize=8.5, labelcolor=INK_2,
               handlelength=1.2, handleheight=1.0, borderaxespad=0)
    fig.subplots_adjust(left=left, right=0.97, top=y_at(1.65), bottom=0.6 / height)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return s


def main() -> None:
    df = load()
    populations = {
        "all": ("All in-use objects in the areaal register", df),
        "quay": ("Quay wall study population (Muur, Kademuur, Beschoeiing, Damwand)",
                 df[df["Objecttype"].isin(QUAY_TYPES)]),
    }
    for key, (label, subset) in populations.items():
        m = by_material(subset)
        out = FIGURES / f"design_life_by_material_{key}.png"
        s = plot(m, label, out)
        print(f"{label}\n  -> {out.relative_to(ROOT)}")
        print(s.assign(share_past=s["share_past"].map("{:.0%}".format),
                       term_share=s["term_share"].map("{:.0%}".format))
               .to_string(index=False))
        print()


if __name__ == "__main__":
    main()
