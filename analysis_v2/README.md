# A second analysis, with the method argued in the open

This folder redoes the burnout and productivity analysis from the raw data. The first pass
(`../project_employee performance analysis.ipynb`) reported what the data showed. This one reports
**how the method was chosen and how the conclusions were checked** — including the conclusions that
did not survive checking.

It is a separate analysis, not a replacement. The two disagree in one place, and the disagreement
is explained below.

**The data is synthetic.** It is a public Kaggle dataset whose inputs were generated independently
of each other. Every number here demonstrates a method; none of it describes a real workforce.

---

## What the analysis found

**Three habits explain how employees differ; fifteen others do not.**
Emotional exhaustion, stress, and hours of deep work account for the entire separation between
groups. Sleep, screen time, doomscrolling, exercise, notifications and ten more habits are at
*identical* averages in every group — the largest difference between any two groups on any of them
is 0.006 of a standard deviation.

This has a direct consequence for recommendations: no group can be told to "sleep more" on the
grounds that its group sleeps less, because no group does. Advice on those habits is company-wide;
only exhaustion, stress and deep work can be targeted per group.

**Job title, work mode and device type explain nothing.**
One-way ANOVA puts eta-squared at 0.00000 for all three against both outcomes (p between 0.36 and
0.93). They are useful for filtering a report; they are not drivers and are excluded from every
model.

**Deep work is associated with much higher output and with no more burnout.**
Output rises from 51 to 98 out of 100 across the range of deep-work hours, while burnout stays flat
at about 49 across the band where 86% of employees sit. Managers do not face a trade-off between
letting people concentrate and protecting them from burnout — on this data, those are separate
levers.

**One group in ten is burning out while performing well.**
9.8% of employees sit at high exhaustion, high stress *and* high deep work: burnout 67 out of 100,
productivity 76 — above average. They do not appear in any report that looks only at performance.
At the individual level, a risk score that lets strong output offset high burnout leaves out 35,292
people whose average burnout is 89 and average productivity is 89.

### The eight groups, most urgent first

| # | Group | Share | Burnout | Productivity |
|---|---|---|---|---|
| 1 | Exhaustion HIGH / Stress HIGH / Deep work LOW | 10.2% | 68.3 | 54.3 |
| 2 | Exhaustion HIGH / Stress HIGH / Deep work HIGH | 9.8% | 67.1 | 75.6 |
| 3 | Exhaustion HIGH / Stress LOW / Deep work LOW | 10.2% | 53.7 | 60.0 |
| 4 | Exhaustion LOW / Stress HIGH / Deep work LOW | 15.3% | 48.7 | 62.0 |
| 5 | Exhaustion HIGH / Stress LOW / Deep work HIGH | 9.8% | 52.3 | 80.4 |
| 6 | Exhaustion LOW / Stress LOW / Deep work LOW | 15.3% | 33.9 | 67.5 |
| 7 | Exhaustion LOW / Stress HIGH / Deep work HIGH | 14.7% | 47.4 | 81.9 |
| 8 | Exhaustion LOW / Stress LOW / Deep work HIGH | 14.7% | 32.7 | 86.1 |

Groups are defined by splitting each of the three habits at its median. No algorithm is needed to
place someone: three comparisons and you have their group.

---

## How the method was chosen

Candidate methods were scored before anything was fitted (section 2 of the notebook). The scores
are stated as the analyst's judgement rather than dressed up as measurements.

| Question | Chosen | Why |
|---|---|---|
| Which habits move the outcomes? | Multiple linear regression | The inputs are uncorrelated with each other, which removes the usual reason to prefer a regularised or tree-based model. Coefficients read directly as advice. |
| Does job context matter? | ANOVA with eta-squared | Produces a number rather than an impression from a table of means. |
| How should employees be grouped? | K-Means weighted by each habit's link to the outcomes, then replaced by a median-split rule | Equal weighting would build distances mostly out of noise, since most habits are unrelated to the outcomes. |
| Dimensionality reduction? | Rejected (PCA) | PCA compresses correlated variables. These are uncorrelated, so each component would be one original variable in disguise. |

Two checks decided whether the simple model was good enough:

- **Is the straight-line assumption safe?** Gradient boosting beat linear regression by 0.00 on
  burnout and 0.02 on productivity out of sample. The relationships really are close to straight
  lines, so the explainable model ships.
- **Does the clustering earn its separation?** Random 7-way grouping gives eta-squared of 0.0000;
  unweighted K-Means gives 0.048; outcome-weighted K-Means gives 0.298. The weighting is doing real
  work, not producing a circular result.

Final model quality: R² 0.65 for burnout and 0.81 for productivity, on 18 of the 25 habits
(the other seven clear statistical significance at 4.6 million rows but have standardised
coefficients below 0.05, which is noise dressed up as signal by sample size).

---

## Where this disagrees with the first analysis

The first pass used **six** groups. This one uses **eight**, and the reason is a flaw in how the
first pass chose that number.

Choosing k by re-running K-Means with different random seeds on the same data is not sufficient.
A value of k can be perfectly reproducible on one fixed dataset and still fall apart when the
employees change. Adding that second test changes the answer:

| k | Agreement across seeds | Agreement across employee samples |
|---|---|---|
| 5 | 0.99 | 0.62 |
| 6 | 0.97 | 0.47 |
| 7 | 0.74 | 0.74 |
| **8** | **0.98** | **0.98** |
| 9 | 0.67 | 0.71 |

The underlying reason: the structure has eight cells (three habits, two levels each). Forcing seven
groups makes the algorithm merge one cell, and *which* cell gets merged depends on the sample — two
equally good solutions exist, with per-point inertia of 4.11125 and 4.11132. A seed-only test cannot
see this, because on a fixed dataset the coin always lands the same way.

The median-split rule was then compared against K-Means at the same group count, which is the only
fair comparison (eta-squared rises automatically with more groups):

| Method | Groups | eta² burnout | eta² productivity | Reproducible |
|---|---|---|---|---|
| K-Means, k=8 | 8 | 0.3110 | 0.2536 | no — depends on seed and sample |
| Median-split rule | 8 | 0.3030 | 0.2535 | yes, by definition |

The rule gives up 0.008 on burnout separation and nothing on productivity, in exchange for being
deterministic and explainable. The clustering still did the work that mattered: it found *which*
three habits and *how many* groups, without being told either.

---

## What this cannot support

- **Cause.** Everything here is association. Nothing shows that reducing someone's stress would
  reduce their burnout.
- **Targeted lifestyle advice.** Groups do not differ on sleep, screen time, exercise or scrolling.
- **Transfer to real people.** The data is synthetic and its inputs are independent by construction,
  which no real workforce is. Re-run this on real HR data before acting on any of it.
- The grouping rule needs three fields per person; 2% of raw rows are missing deep-work hours and
  cannot be placed. Groups are unequal in size (10% to 15%) because medians of discrete 1–10 scales
  do not split a population evenly.

---

## Verification

The analysis was re-checked in rounds until a round found nothing new. Six rounds were needed, and
they overturned three conclusions — including one that was itself a correction of an earlier
mistake. Section 9 of the notebook lists every one, with the number that disproved it.

They are kept in the record deliberately. An analysis that reports only its final state gives a
reader no way to judge how hard it was tested.

---

## Files

```
analysis_v2.py        source, in jupytext percent format
analysis_v2.ipynb     the executed notebook — all 26 cells run on 4.6M employees, no errors
figures/              four charts, red and blue on white
tables/               seven CSV outputs
```

## Running it

From this folder, with the project virtual environment active:

```bash
python -m jupytext --to notebook analysis_v2.py -o analysis_v2.ipynb
python -m jupyter nbconvert --to notebook --execute --inplace analysis_v2.ipynb
```

Takes about 20 minutes on the full dataset. Set `NB_NROWS=300000` for a two-minute test run; the
group count and the conclusions come out the same.
