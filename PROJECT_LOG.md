# Project log

This file records how this project was built: the environment, the order of work, the
decisions made along the way, and the mistakes that were fixed. `README.md` presents the
findings for a business reader; this file is the implementation diary behind it, for anyone
(including a future version of the author) who needs to pick the project back up or understand
why a design choice was made.

## 1. Environment

- **Python:** 3.11.9, on Windows. (`statsmodels` was added later, during the second analysis —
  see that section below. `requirements.txt` now pins 145 packages.)
- **Virtual environment:** created with `python -m venv venv` at the project root. It is not
  committed to Git (see `.gitignore`); each person who clones the repo creates their own.
- **Packages:** pinned in `requirements.txt` (140 packages, generated with `pip freeze`). The
  packages fall into four groups:

  | Group | Packages | Used for |
  |---|---|---|
  | Data workflow | `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyarrow` | loading the CSV in a memory-efficient way, building the problem indices, K-Means/GMM/Ward clustering, the Phase 2 regression |
  | Notebooks | `jupyterlab`, `notebook`, `ipykernel`, `jupytext`, `nbconvert` | writing and executing the two `.ipynb` notebooks from the command line |
  | Charts and reports | `matplotlib`, `seaborn`, `openpyxl` | the static PNG figures and the `report.xlsx` workbook (with live formulas) |
  | Data download | `kaggle` | pulling the source dataset by API instead of a manual download |

  Three packages (`plotly`, `altair`, `streamlit`) are also pinned in `requirements.txt` because
  a browser-based dashboard was considered early on. The project ended up using a single static
  HTML file (`visualize/report.html`, plain JavaScript, no framework) instead, so these three are
  not imported anywhere in the current code. They are left in `requirements.txt` rather than
  removed, in case an interactive dashboard is revisited later; `pip install -r requirements.txt`
  still reproduces the exact environment either way.

- **To recreate the environment from scratch:**
  ```bash
  python -m venv venv
  venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
  pip install -r requirements.txt
  ```
  Verified on 2026-09-23: the installed environment matches `requirements.txt` exactly
  (`pip freeze` produces no diff against the file), so the pin file is trustworthy as-is.

## 2. Timeline

### Phase 0 — Environment and data
Set up the virtual environment and installed the packages above. Downloaded the source dataset
(Kaggle, "Digital Burnout and Productivity Analytics", 5,000,000 rows, 34 columns, synthetic
data — the author states the fields were generated, not collected from real employees) into
`data/raw/`, which is excluded from Git for size reasons.

### Phase 1 — Discovering the problems and grouping employees
1. **Data exploration.** Loaded the CSV with explicit `float32` / `int16` / `category` dtypes to
   keep the 5M-row table under 1 GB in memory, then printed schema, summary statistics, and
   correlations (`reports/01_*.csv`).
2. **Defining "problems."** Built five problem indices from the 25 behavioural columns —
   digital overload, recovery deficit, focus capacity, psychological strain, environment
   quality — each with a defined direction (`PROBLEM_SIGN` in `src/segmentation.py`) so that
   "higher index = more of a problem" is consistent across indices built from columns that point
   in different raw directions (e.g. more sleep is good, more screen time is bad).
3. **Grouping employees (clustering).** Used K-Means on the five indices to split employees into
   groups. The first version weighted all five indices equally; a stability check (running the
   same K-Means with five different random seeds and comparing the groupings with the Adjusted
   Rand Index) showed this was not reproducible — see the "equal-weight clustering" entry in
   Section 3. After fixing the weighting, `k = 6` groups were chosen by stability rather than by
   silhouette score, and validated against a held-out sample, a Gaussian mixture model, and
   hierarchical (Ward) clustering — see the validation table in `README.md`.
4. **Risk scoring.** Combined burnout and productivity into a single risk score per group so
   groups could be ranked and labelled (Low / High / Very high) — see the "risk score" entry in
   Section 3 for a bug that was caught and fixed here.
5. **Within-group correlation.** For the groups sharing the same risk level, compared how the
   same input factors relate to outcomes differently inside each group (`reports/04_within_group_correlation.csv`)
   — this surfaces a Berkson's-paradox-style effect: a factor can correlate one way across the
   whole population and the opposite way inside a single group.
6. **Notebook.** All of the above was written as `project_employee performance analysis.ipynb`,
   split into cells by analysis step, and executed end to end on the full 5M rows (no errors).

### Phase 1 — Reports and dashboard
Built two output artifacts from the notebook's results, both in `visualize/`:
- `report.html` — a single-file interactive report (filters for group, risk level, occupation,
  work mode) that recomputes summary statistics and correlations in the browser using a
  pre-aggregated "cube" (126 cells: 6 groups × 7 occupations × 3 work modes, storing centred
  sums and cross-products), so the whole 5M-row dataset never has to be shipped to the browser.
- `report.xlsx` — a 7-sheet workbook (Summary, Workplace problems, Groups, Warning signs by
  group, Groups within a risk level, Actions, Method) built with `openpyxl`, using live formulas
  (not hardcoded numbers) so the sheet recalculates if the underlying numbers are edited. All 337
  formulas were checked with the `formulas` Python package (0 errors) since LibreOffice was not
  available locally to recalculate them directly.

### Presentation standards
Partway through Phase 1, a standing instruction was set for every reader-facing deliverable in
this project: **English, plain wording, no exaggerated claims, a red-and-blue theme on a white
background, and a small black cat illustration in each deliverable's opening section.** This was
applied retroactively to the notebook, the README, `report.html`, and `report.xlsx`, and has been
followed in every deliverable produced since (Phase 2 report, presentation deck). It is saved as
a standing preference so it is not re-explained in future sessions.

### Publishing to GitHub
Initialised the local repository, wrote `.gitignore` (excluding raw/processed data, the virtual
environment, notebook checkpoints, and IDE files), and pushed to `origin/main`. The GitHub remote
already had an initial commit with its own README, so the merge used
`--allow-unrelated-histories -X ours` to keep this project's full README rather than GitHub's
placeholder.

### Phase 2 — Root causes and personal solutions
Requested once the groups from Phase 1 were in place, to move from "which groups exist" to
"what to actually do about each one," and to avoid generic advice such as "run a training
course." Three parts:
1. **Survey design.** `phase2/survey_questionnaire.md` — a follow-up questionnaire (hypotheses
   H1–H12 plus four screening questions, sampling target of about 385 responses per group,
   built from validated scales: BAT for burnout, PSS-10 for stress, REQ for recovery experience,
   IPAQ for physical activity) to actually test, on real employees, the lifestyle differences the
   dataset only lets us guess at.
2. **Root-cause frameworks.** Applied nine established problem-analysis models (5 Whys,
   Fishbone/Ishikawa, SWOT, the Job Demands–Resources model, the Effort–Reward Imbalance model,
   Areas of Worklife, the Stressor–Detachment model, COM-B, and Self-Determination Theory) to the
   group characteristics from Phase 1, to derive plausible root causes. Every root cause is
   tagged `[data]` (supported by a pattern actually observed in this dataset) or `[test]`
   (a hypothesis the survey above is designed to check) — the dataset is synthetic, so no root
   cause is presented as proven.
3. **Personal solutions with citations.** For each group, researched psychology and occupational
   health sources (WHO, peer-reviewed studies, established scale documentation) to propose
   routines suited to that group's characteristics, with a cost/benefit comparison for changing
   habits. All sources are cited with working links and were checked before being quoted —
   see `phase2/PHASE2_REPORT.md` (38 numbered references).
4. **Supporting notebook.** `phase2/phase2_lifestyle_root_causes.ipynb` builds the lifestyle
   profile tables, checks the guideline gaps, fits the burnout/productivity regression model used
   for the what-if estimates, and draws the fishbone diagrams and routine timelines used in the
   report.

### Phase 3 — Presentation for a general audience (in progress)
Requested to turn the analysis into a short slide deck for people with no background in data or
code, from the point of view of a project manager reporting progress. Being built as an Artifact
slide deck (white background, red/blue accents, the same black cat illustration as the other
deliverables). As of this log entry, 4 of an planned 18 slides are drafted
(cover, why this matters, what data was used, the scale of the problems); the remaining slides
(root causes, the six groups, the group map, a same-risk comparison, suggested routines,
cost/benefit, what to expect, the rollout plan, what is being asked of leadership, limitations,
closing) are still to be written.

### Second analysis (`analysis_v2/`)
Requested as a full redo from the raw data, working the way an analyst would when handed the
dataset cold: explore first, compare candidate methods and defend the choice before fitting
anything, write an execution plan, and stop for confirmation at every stage rather than running
straight through.

The stage-by-stage structure was the user's instruction and it earned its keep — three separate
stages produced a result that contradicted what the previous stage had assumed, and stopping to
check is what caught them. The work then went through a verification loop, re-checking its own
output until a round produced no new corrections; six rounds were needed. `analysis_v2/README.md`
carries the findings and `analysis_v2/analysis_v2.ipynb` section 9 carries the full log.

The substantive results that differ from Phase 1:

- **Eight groups, not six.** Choosing the number of groups by seed-stability alone is insufficient:
  a k can be perfectly reproducible on one fixed dataset and collapse when the employees change.
  Adding a second test — fit on independent subsets and compare — moved the answer from k=7 (which
  had looked best on the old criterion) to k=8, which is the natural count because the structure is
  three habits at two levels each.
- **A median-split rule replaces the algorithm for the deliverable.** Compared fairly at the same
  group count, K-Means separates the outcomes very slightly better (eta-squared 0.311 vs 0.303 on
  burnout, tied on productivity), but the rule is deterministic and can be applied by hand. The
  clustering still earned its place by discovering which three habits and how many groups.
- **A limit on what segmentation can deliver.** The fifteen habits outside the three defining ones
  are at identical averages in every group, so per-group lifestyle advice is not supportable on this
  data. Those actions are company-wide.
- **A weaker, defensible claim about deep work.** It is associated with much higher output and with
  no increase in burnout — not with a reduction in burnout, which an earlier draft had claimed using
  a coefficient the analysis had already ruled out as too small to matter.

`statsmodels` was added to the environment during this phase, for regression coefficients with
confidence intervals and p-values.

## 3. Key decisions and fixes

- **Equal-weight clustering was not reproducible.** The first K-Means model weighted the five
  problem indices equally. Running it five times with different random seeds gave noticeably
  different groupings (Adjusted Rand Index ≈ 0.33 between runs) — not stable enough to base
  recommendations on. Fix: weight each index by how strongly it relates to the two outcomes that
  actually matter (burnout and productivity), instead of treating all five as equally important.
  This raised seed-to-seed stability to ARI ≈ 0.92.
- **The risk score let high output cancel out high burnout.** One group had both high burnout and
  high productivity, but the original risk score (a weighted average) came out looking "stable"
  because the two effects offset each other — masking a group that is likely burning out while
  still performing. Fix: changed the score to add only the *harmful* side of each measure
  (`clip(z_burnout, 0) + clip(z_productivity_gap, 0)`), so strong output no longer hides high
  burnout.
- **"Reliable levers" briefly included two factors with no real relationship to outcomes.** Two
  candidate factors (motivation, mental fatigue) had a population-wide correlation close to zero,
  meaning their apparent "direction" was noise, not a signal. Fix: added a minimum
  correlation-strength filter (`|r| >= 0.05`) before treating any factor as an actionable lever.
- **Caffeine units could not be confirmed.** The dataset does not document what unit the caffeine
  column is measured in, and the source page could not be reached to check. Rather than assume
  a unit, the label was changed to "Caffeine intake (per day, unit not stated)" everywhere it
  appears, and both notebooks and both reports were rebuilt after the change.
- **The dataset is synthetic.** This is stated by the dataset's own author (input fields are
  close to statistically independent, all pairwise correlations under 0.01) and is repeated in
  every deliverable — the README's limitations section, the Phase 2 report's root-cause tags, and
  the deck's "practice data" note — so nobody downstream mistakes these numbers for a finding
  about a real workforce.
- **Merging with the GitHub remote's placeholder commit.** `git push` was rejected because the
  remote already had its own initial commit and README. Resolved with
  `git merge --allow-unrelated-histories -X ours origin/main`, which keeps this project's README
  in any line both sides touched.

## 4. Known limitations (carried into every deliverable)

- Synthetic data: treat every number here as a demonstration of the method, not a finding about
  a real workforce, until the same steps are re-run on real HR data.
- Correlation, not causation: nothing in Phase 1 or Phase 2 proves that a habit *causes* burnout
  or lower productivity, only that they tend to appear together.
- Warning-sign thresholds (e.g. "sleep under 6 hours") are analysis choices, not medical
  cut-offs, and can be adjusted.
- Root causes in the Phase 2 report are explicitly split into `[data]` (pattern seen in this
  dataset) and `[test]` (needs the follow-up survey to confirm) — none are asserted as proven.

## 5. Picking the project back up

If returning to this project after a break:
1. Recreate the environment (Section 1) and re-download the dataset (see `README.md`,
   "How to reproduce") — raw data and the venv are both excluded from Git.
2. Read `README.md` for the Phase 1 findings, `phase2/PHASE2_REPORT.md` for the Phase 2 root
   causes and recommendations, and this file for how they were produced.
3. The presentation deck (Phase 3) is unfinished — see Section 2 for which slides remain.
