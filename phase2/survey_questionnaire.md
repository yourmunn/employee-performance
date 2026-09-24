# Follow-up survey: lifestyle and root causes

The Phase 1 data shows *which* problems each employee group has, but not *why* (see the
[Phase 2 report](PHASE2_REPORT.md), section 2). This questionnaire is designed to collect the missing information in
a real organisation: daily routines that the dataset does not record, and the work conditions behind each group's
problems.

Every question is linked to a **hypothesis (H)** from the root-cause analysis, so each answer has a clear use.

## 1. Hypotheses to test

| Code | Hypothesis | Groups | Framework behind it |
|---|---|---|---|
| H1 | Workload is higher than the time available | N1, N4 | Job Demands–Resources [5]; Areas of Worklife [7]; Gallup causes [11] |
| H2 | Priorities or role are unclear | N1, N3 | Gallup causes [11]; Areas of Worklife [7] |
| H3 | Effort is not matched by recognition or reward | N1, N4 | Effort–Reward Imbalance [6] |
| H4 | People are expected to answer messages outside working hours | N2, N4 | Becker et al. [32] |
| H5 | Late-night device use is partly work (catching up on messages) | N2 | Stressor–Detachment model [8] |
| H6 | The phone stays in the bedroom and default alerts are on | N2 | CDC sleep tips [13] |
| H7 | Scrolling is used to unwind from stress | N2 | COM-B (automatic motivation) [9] |
| H8 | A quick-reply chat culture causes frequent task switching | N3, N1 | Task-switching research [22, 23, 24] |
| H9 | There is no protected time for focused work | N3, N1 | Perlow [26] |
| H10 | Planning and prioritising skills are a gap | N3 | COM-B (psychological capability) [9] |
| H11 | People find it hard to switch off after work | N4 | Stressor–Detachment model [8] |
| H12 | Strong performers are given more work | N4 | Effort–Reward Imbalance [6]; Gallup [11] |
| S1–S4 | Shared base: sleep timing, caffeine timing, activity, stress | All | AASM [12], CDC [13], Drake [14], WHO [17] |

Reference numbers match the [Phase 2 report](PHASE2_REPORT.md#references).

## 2. Survey design

- **Who:** all employees, with the Phase 1 group code attached by HR so that answers can be compared between groups.
  Answers are anonymous to managers; only aggregated results by group (minimum 20 people per cell) are reported.
- **Sample size:** to estimate a share within ±5 percentage points at 95% confidence, each group needs about
  385 responses (n = 1.96² × 0.5 × 0.5 / 0.05² ≈ 384). With six groups, aim for about 2,300 completed surveys.
- **Length:** about 12 minutes. Pilot it with 20–30 people first, and remove or reword questions that cause confusion.
- **Validated scales:** where a published scale exists, use it instead of writing new questions. Check each scale's
  terms of use before using it.
  - Burnout: Burnout Assessment Tool, BAT ([website](https://burnoutassessmenttool.be/start_eng/)) [36]
  - Stress: Perceived Stress Scale, PSS-10 ([Carnegie Mellon lab page](https://www.cmu.edu/dietrich/psychology/stress-immunity-disease-lab/scales/index.html)) [37]
  - Switching off after work: detachment subscale of the Recovery Experience Questionnaire [33]
  - Physical activity: IPAQ short form [38]
- **Analysis plan:** for each hypothesis, compare the share of "agree / often" answers between groups (chi-square test
  or logistic regression with group as the predictor). A hypothesis is supported for a group if its rate is clearly
  higher than in the low-risk groups (N5, N6).

## 3. Questionnaire

Scale A: *Strongly disagree · Disagree · Neutral · Agree · Strongly agree*
Scale F: *Never · Rarely · Sometimes · Often · Always*

### Part A — Workload and priorities

| # | Question | Answer | Tests |
|---|---|---|---|
| A1 | On a typical workday, how many hours do you actually work (including evenings)? | Number | H1 |
| A2 | I can finish my work within my normal working hours. | Scale A | H1 |
| A3 | I know which of my tasks matter most this week. | Scale A | H2 |
| A4 | I often receive tasks with conflicting priorities. | Scale F | H2 |
| A5 | The effort I put into my work is fairly recognised. | Scale A | H3 |
| A6 | When I do good work, I am given more work rather than support or recognition. | Scale A | H3, H12 |
| A7 | In the last month, how many times did your manager talk with you about your workload? | 0 / 1 / 2–3 / 4+ | H1, H2 |

### Part B — Messages and after-hours contact

| # | Question | Answer | Tests |
|---|---|---|---|
| B1 | My team expects me to reply to messages outside working hours. | Scale A | H4 |
| B2 | How often do you read work messages after 9 pm? | Scale F | H4, H5 |
| B3 | When you use your phone late at night, what is it mostly for? | Work / Personal / Both | H5 |
| B4 | Do you keep notifications on for all apps? | All on / Some off / Batched or scheduled / All off | H6 |
| B5 | Where does your phone stay while you sleep? | Bedside / Elsewhere in bedroom / Outside bedroom | H6 |
| B6 | I use my phone to relax when I feel stressed. | Scale F | H7 |
| B7 | I scroll longer than I planned. | Scale F | H7 |

### Part C — Focus and task switching

| # | Question | Answer | Tests |
|---|---|---|---|
| C1 | During a typical day, how many times are you interrupted while working on a task? | 0–5 / 6–15 / 16–30 / 30+ | H8 |
| C2 | I am expected to reply to chat messages within a few minutes. | Scale A | H8 |
| C3 | I have at least one block of 60 minutes or more without meetings or messages on most days. | Scale A | H9 |
| C4 | My calendar allows me to block time for focused work. | Scale A | H9 |
| C5 | I plan my day before I start working. | Scale F | H10 |
| C6 | I find it hard to decide what to work on first. | Scale F | H10 |

### Part D — Switching off and recovery

| # | Question | Answer | Tests |
|---|---|---|---|
| D1 | Detachment subscale of the Recovery Experience Questionnaire (4 items) | Published scale | H11 |
| D2 | I have a fixed time when my workday ends. | Scale A | H11 |
| D3 | What do you usually do in the first hour after work? | Open text | H7, H11 |

### Part E — Daily routine (shared base)

| # | Question | Answer | Tests |
|---|---|---|---|
| E1 | On workdays, what time do you usually go to bed and get up? | Two times | S1 |
| E2 | On days off, what time do you usually go to bed and get up? | Two times | S1 (regularity) |
| E3 | What time is your last caffeinated drink on a typical day? | Time or "none" | S2 |
| E4 | How many caffeinated drinks do you have on a typical day, and what kind (coffee, tea, energy drink)? | Number + type | S2 |
| E5 | IPAQ short form (7 items) | Published scale | S3 |
| E6 | Perceived Stress Scale (10 items) | Published scale | S4 |
| E7 | Burnout Assessment Tool, short version | Published scale | Outcome |

### Part F — Readiness to change and preferred support (COM-B)

| # | Question | Answer | COM-B part |
|---|---|---|---|
| F1 | Which one change would help you most? | List of the routine changes in the report + "Other" | — |
| F2 | I know how to make that change. | Scale A | Capability |
| F3 | My work allows me to make that change. | Scale A | Opportunity |
| F4 | I want to make that change in the next month. | Scale A | Motivation |
| F5 | What would make it easier? | Tools / Manager support / Team agreement / Training / Other | — |

### Part G — Context (optional)

| # | Question | Answer | Why |
|---|---|---|---|
| G1 | Do you care for children or other family members on workdays? | Yes / No / Prefer not to say | Context for sleep and after-hours use |
| G2 | One-way commute time | Minutes | Context for available time |

## 4. How the results are used

1. Confirm or reject each hypothesis per group (section 2, analysis plan).
2. Keep only the routine changes whose cause is confirmed for that group, and add work-level changes where the cause
   is in the job itself (for example H1, H3, H4). Personal routines alone cannot fix a workload problem; the WHO
   describes burnout as the result of chronic *workplace* stress that has not been managed [1].
3. Use Part F to choose the first change for each person: the one with the highest motivation and the fewest
   capability or opportunity barriers.
