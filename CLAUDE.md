# Notes for agents

## Syncing `report/` with Overleaf

`report/` is the group's Overleaf project (TU Delft report template), kept as a
git subtree. Teammates edit it in the Overleaf editor, and their edits arrive as
commits on the Overleaf side.

- Remote: `overleaf` = `https://git@git.overleaf.com/6aa142900f2a5438306bc48f`
- Branch: **`main`** (not `master`)
- Token: `OVERLEAF_TOKEN=...` in `.env` at the repo root (git-ignored)

### Token rules

- Never print, `cat`, `echo` or log the token or the contents of `.env`. Never
  copy it into another file, a remote URL or git config.
- Don't run `git credential fill`, `GIT_TRACE`, `GIT_CURL_VERBOSE` or similar
  without masking the output. To check the token is there, print only its length
  and whether it starts with `olp_`.
- Never stage `.env`. Check with `git check-ignore -v .env` if in doubt.

### Check the setup (fresh clone or new machine)

```bash
git remote get-url overleaf          # should be the URL above, with no token
git config --local --get-all credential.https://git.overleaf.com.helper
```

The helper list should be an empty line, then the function below. If it is
missing, ask the user, then set it up. Because of the quotes, write the
function to a temp file and pass it with `"$(cat file)"`:

```bash
git remote add overleaf https://git@git.overleaf.com/6aa142900f2a5438306bc48f
git config --local --add credential.https://git.overleaf.com.helper ""
git config --local --add credential.https://git.overleaf.com.helper "$(cat /path/to/helper.txt)"
```

Contents of `helper.txt` (one line):

```
!f() { test "$1" = get || exit 0; root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0; test -f "$root/.env" || exit 0; token=$(awk -v q="'" 'sub(/^[ \t]*(export[ \t]+)?OVERLEAF_TOKEN[ \t]*=[ \t]*/, "") { sub(/[ \t\r]+$/, ""); if ($0 ~ /^".*"$/ || $0 ~ ("^" q ".*" q "$")) $0 = substr($0, 2, length($0) - 2); print; exit }' "$root/.env"); test -n "$token" || exit 0; echo username=git; echo "password=$token"; }; f
```

The empty first entry clears the system `osxkeychain` helper for Overleaf only,
so the token is never stored in the macOS Keychain.

### Where things go in `report/`

- `report.tex` is the main file. It `\input`s `mainmatter/chapter-1.tex` to
  `chapter-4.tex`, the conclusion, and the appendices in `appendix/`. A new
  section goes inside the right chapter file. A new file needs an `\input` in
  `report.tex` or in its chapter.
- Figures go in `report/figures/`. Bibliography entries go in `report/report.bib`
  (biblatex with biber, so cite with `\cite{key}`).
- The class is `tudelft-report.cls`. Don't edit it.

### Build before pushing

Every push must build. Overleaf compiles whatever is pushed, and a broken build
blocks all six authors. The Overleaf project compiles with **XeLaTeX**, so build
with XeLaTeX too. With XeLaTeX the class uses the TU Delft house fonts (Arial and
Roboto Slab Light/Thin). With pdfLaTeX it falls back to Palatino.

```bash
export PATH="/Library/TeX/texbin:$PATH"   # MacTeX; may be missing from the agent's shell
cd "$(git rev-parse --show-toplevel)/report"
out="${TMPDIR:-/tmp}/overleaf-build"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$out" report.tex
grep -nE '^[^ ]+:[0-9]+: |^! |undefined|not found' "$out/report.log" | grep -v Info
grep -nE 'ERROR|WARN' "$out/report.blg"
```

- A full build takes about 45 s.
- Build once before you edit and keep the warning list, so you can tell your
  warnings from existing ones. On 2026-10-30 the Overleaf version already had
  15 undefined references or citations (bib keys `jcss2001`,
  `utrecht_programmaplan`, `amsterdam_brief` and `amsterdam_tender` are missing
  from `report.bib`), 2 biber warnings about non-numeric years, and a
  font-shape warning for bold Roboto Slab Light.
- On macOS, XeLaTeX finds fonts by name only when they are installed in the
  system. Arial ships with macOS. On this Mac, Roboto Slab Light and Thin were
  copied from TeX Live to `~/Library/Fonts`. If the build stops with
  `The font "Roboto Slab Light" cannot be found` on another machine, ask the
  user, then copy `RobotoSlab-Light.otf` and `RobotoSlab-Thin.otf` from
  `$(kpsewhich -var-value TEXMFDIST)/fonts/opentype/google/roboto/` to
  `~/Library/Fonts` and wait a few seconds before rebuilding. Don't change the
  class or switch to pdfLaTeX to get around it.
- `-outdir` keeps all build files outside the repo. Never commit `.aux`,
  `.log`, `.bbl`, `.pdf` or other build output into `report/`.
- Push only if `latexmk` exits with 0 and the text you wrote has no undefined
  references, undefined citations or missing files.
- If warnings come from teammates' text, don't fix them. List them for the user.

### Pull and push

```bash
# get Overleaf edits; needs a clean working tree. Refresh the index first:
# git subtree checks with git diff-index, which can see a file you just wrote
# as modified
git update-index -q --refresh
git subtree pull --prefix=report overleaf main

# see what a push would send
git log --oneline overleaf/main..$(git subtree split --prefix=report)

# push: pull first, build again (see above), and ask the user before every push
git update-index -q --refresh
git subtree pull --prefix=report overleaf main
git subtree push --prefix=report overleaf main
```

- After a push, the next pull adds a merge commit that changes no files. This
  is expected with subtree and keeps later pushes fast.

- If the working tree is dirty, ask the user whether to commit or stash. Don't
  decide yourself.
- If a subtree pull has merge conflicts (a teammate edited the same lines in
  Overleaf), show the conflicts to the user and resolve them together. Never
  resolve them by discarding the Overleaf side.
- Never force push to `overleaf`, and never use `--squash`, because it breaks
  later subtree pulls and pushes.
- If a push is rejected as non-fast-forward, someone edited in Overleaf: pull
  again, then push.
- Keep changes to `report/` in their own commits. Their messages become the
  Overleaf history.
- Scripts write plots to `figures/`, but the report reads from
  `report/figures/`. Copy a regenerated figure there when the report should use
  it.

## Course context (Google Drive)

The course folder in the user's Google Drive is linked to the Claude desktop
space "CME4150 - Managing Uncertainty and Data". Use it as background when
writing for the report. Find it with:

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
- Which source wins: `report/` (Overleaf) first, then this repo (scripts,
  `data/processed/`, `docs/`), then this folder. Use the older drafts
  for ideas and sources only. Never let them overwrite newer text in `report/`.
- Don't copy course PDFs or the TNO report into the repo or into `report/`: the
  repo is on GitHub and the Overleaf project is shared. Cite them instead.
- Google Drive may keep files online-only, and a read can time out. If it does,
  ask the user to make the folder available offline in Google Drive.
- The instructions, knowledge files and chats of the desktop space live on
  claude.ai. Claude Code can't reach them.
