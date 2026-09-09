# CME4150 Team Challenge - quay walls Utrecht

Code and data for the team challenge on strategic programming of maintenance,
strengthening and replacement of quay walls in the Municipality of Utrecht.

## Layout

```
notebooks/       analysis, one notebook per report section
data/raw/        downloaded source data, never edited by hand
data/processed/  everything produced by the notebooks
figures/         plots exported for the report
```

Notebooks map to the report sections:

| Notebook | Report section |
|---|---|
| `01_data.ipynb` | 1.2 assumptions, data collection & generation |
| `02_exploration.ipynb` | 1.3 problem exploration and dimension reduction |
| `03_probabilistic_models.ipynb` | 2.1 probabilistic models |
| `04_fault_tree.ipynb` | 3.1 fault tree |
| `05_decision_tree.ipynb` | 3.2 trade-off analysis |
| `06_regression.ipynb` | 4.1 regression |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

## Working together

- One person per notebook where possible. Notebooks merge badly, so avoid two
  people editing the same one at the same time.
- Run "Restart kernel and run all" before committing, so outputs match the code.
- Anything a notebook writes goes to `data/processed/` or `figures/`, so it can
  always be regenerated from `data/raw/`.
- Note the source and download date of every file in `data/raw/` in
  `data/raw/SOURCES.md`.

## Data sources

See `data/raw/SOURCES.md`.
