"""The green / orange / red screening of the quay walls in the asset register.

Follows every wall in the municipal asset register through the decision tree
of the report (Figure 1.2):

  1. Past design life?   No  -> GREEN
  2. Masonry wall?       No  -> ORANGE
                         Yes -> calculate Pf; RED if Pf > Pf,target, else ORANGE

A wall is past its design life when `Eindjaar` (the register's theoretical end
year, Aanlegjaar + design life; 80 years for every walmuur) is before
REFERENCE_YEAR, the current year. It is masonry when `Bouwmateriaal` lists
Metselwerk.

Choices, all set as constants below:
  * only Status "In gebruik",
  * `Eindjaar` missing, or at or before `Aanlegjaar` (entry errors), ends in
    "not classified", because the tree has no rule for it,
  * an object with no material recorded counts as not masonry,
  * KM060028 has Aanlegjaar 2118, a year in the future, read as 2018,
  * a walmuur renewed on steel is screened from its renewal year
    (walmuur_foundation.csv, with_renewals), since the register keeps the
    year of the old wall. Only the walmuren have foundation data, so the
    register keeps the register years.

The other scripts import the register (load), the walmuren and the colours from
here. Run on its own, it prints the objects and length per class for the quay
wall study population of the register (Muur, Kademuur, Beschoeiing, Damwand) and
for the 51 walmuren of the Wervengebied, on the register year and from the
renewal year (Appendix A).
Run: python scripts/screening.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AREAAL = ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json"
FOUNDATION = ROOT / "data" / "processed" / "walmuur_foundation.csv"

REFERENCE_YEAR = 2026
STATUS = "In gebruik"
QUAY_TYPES = ["Muur", "Kademuur", "Beschoeiing", "Damwand"]
YEAR_FIXES = {"KM060028": 2018}      # Aanlegjaar 2118 is a typo for 2018

CANALS = {"Oude Gracht": "Oudegracht", "Nieuwe Gracht": "Nieuwegracht",
          "Kromme Nieuwe Gracht": "Kromme Nieuwegracht"}

# Colours: status palette (good / warning / critical, CVD checked). Orange is
# drawn amber, as in the report's flowchart.
GREEN = "#0ca30c"
ORANGE = "#fab219"
RED = "#d03b3b"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"

CLASSES = ["green", "orange", "pf", "unclassified"]


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


def summary(c: pd.DataFrame) -> str:
    s = c.groupby("cls").agg(objects=("cls", "size"), length_m=("Lengte", "sum"))
    s = s.reindex([k for k in CLASSES if k in s.index])
    s.loc["total"] = s.sum()
    s["share_length"] = (s["length_m"] / s.loc["total", "length_m"]).map("{:.0%}".format)
    s["length_m"] = s["length_m"].round()
    return s.astype({"objects": int}).to_string()


def main() -> None:
    df = load()
    w = walmuren(df)
    for title, c in (("Register, quay wall study population", register(df)),
                     ("Walmuren, register year", w),
                     ("Walmuren, renewed walls from their renewal year", with_renewals(w))):
        print(f"{title}\n{summary(c)}\n")


if __name__ == "__main__":
    main()
