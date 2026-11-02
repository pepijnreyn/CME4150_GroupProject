# Notes for agents

## The report

The report was submitted on 2026-11-01. Its LaTeX source, the group's Overleaf
project kept in `report/` as a git subtree, was removed from the repo on
2026-11-02. It is in the git history up to commit `f823887`: read a file with
`git show f823887:report/<path>`.

- The report links this repo as its source code. Keep every script it names,
  the data those scripts read and the outputs it quotes. After changing a
  script, rerun it and check that its outputs in `data/processed/` and
  `figures/` are unchanged, unless the change is meant to change them.
- The `overleaf` remote may still be set up in `.git/config`. Don't pull from
  it or push to it: a subtree pull would bring `report/` back.

### Token rules

`.env` at the repo root (git-ignored) still holds `OVERLEAF_TOKEN`.

- Never print, `cat`, `echo` or log the token or the contents of `.env`. Never
  copy it into another file, a remote URL or git config.
- Never stage `.env`. Check with `git check-ignore -v .env` if in doubt.

## Course context (Google Drive)

The course folder in the user's Google Drive is linked to the Claude desktop
space "CME4150 - Managing Uncertainty and Data". Use it as background for
questions about the report. Find it with:

```bash
ls -d ~/Library/CloudStorage/GoogleDrive-*/"Mijn Drive/Construction Management and Engineering/CME4150 - Managing Uncertainty and Data"
```

| File | What it is |
|---|---|
| `TeamChallange.pdf` | The assignment: required sections, criteria and limits. |
| `W1.2- Team Challenge Description_Gemeente Utrecht_2026.pdf` | The Municipality of Utrecht's brief |
| `W1.1 - Introduction_020926.pdf` | Course introduction lecture |
| `Planning_TeamChallenge_CME4150.docx` | Team planning: who writes what, and by when |
| `Eindrapport_Bewezen-sterkte_TNO_Deltares_SmartPort_final.pdf` | Proven-strength report by TNO, Deltares and SmartPort (23 MB) |
| `1-1_Assets_in_scope_northern_Stadsbuitengracht.md`, `latex/section_1_1.tex` | Drafts of section 1.1 (2026-09-11) |
| `failure_formula_notes.md` / `.tex` | September notes on the Hemel et al. pile-bending formula. They differ from `docs/failure_formula_notes.md`. The current model is `scripts/StressCaclulation/FailureProbability.py`. |
| `decision_tree_wall_category.tex` / `.pdf` | Decision tree for wall categories |
| `Claude outputs/` | Older drafts from the Claude desktop app (sections 1.1, 1.2.4, 3.1, appendices, `quay_model.py`) |
| `CME4150 - Group project notes.gdoc` | Only a link to a Google Doc. Its text isn't on disk, so ask the user if you need it. |

- The folder is read-only for agents. Never edit, move or delete anything in it,
  because it syncs to the user's Google Drive.
- Which source wins: the submitted report (`f823887:report/`) first, then this
  repo (scripts, `data/processed/`, `docs/`), then this folder. Use the older
  drafts for ideas and sources only.
- Don't copy course PDFs or the TNO report into the repo: it is on GitHub.
  Cite them instead.
- Google Drive may keep files online-only, and a read can time out. If it does,
  ask the user to make the folder available offline in Google Drive.
- The instructions, knowledge files and chats of the desktop space live on
  claude.ai. Claude Code can't reach them.
