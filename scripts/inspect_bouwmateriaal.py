"""List the material values that occur in the areaal file's `Bouwmateriaal`.

The field is free-ish text and multi-value: one object can read
"Metselwerk, Hout". So this prints three things:

  1. how often the field is filled at all,
  2. the raw values exactly as stored, combinations included,
  3. the individual materials after splitting on commas, which is the list
     you want when grouping objects by material.
"""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREAAL = ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json"

FIELD = "Bouwmateriaal"


def main() -> None:
    features = json.loads(AREAAL.read_text())["features"]

    raw = Counter()
    single = Counter()
    empty = 0

    for feature in features:
        value = (feature.get("properties") or {}).get(FIELD) or ""
        value = value.strip()
        if not value:
            empty += 1
            continue
        raw[value] += 1
        for part in value.split(","):
            part = part.strip()
            if part:
                single[part] += 1

    total = len(features)
    filled = total - empty
    print(f"{FIELD} in {AREAAL.name}")
    print(f"  {total} features, {filled} filled ({filled / total:.0%}), {empty} empty")
    print(f"  {len(raw)} distinct stored values, {len(single)} distinct materials\n")

    print(f"Individual materials ({len(single)}):")
    for name, count in single.most_common():
        print(f"  {count:5d}  {name}")

    combos = {v: c for v, c in raw.items() if "," in v}
    print(f"\nCombinations ({len(combos)}):")
    for name, count in sorted(combos.items(), key=lambda kv: -kv[1]):
        print(f"  {count:5d}  {name}")


if __name__ == "__main__":
    main()
