"""Definitions shared by the analysis notebook and the report builders.

Five problem indices condense the 25 behavioural columns; each index keeps the sign of its
members so that a high value always means "more of this", and PROBLEM_SIGN turns any index
into a "higher = worse" reading for profiling.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from config import CLUSTER_FEATURES

# index -> {column: sign}; sign +1 means a higher raw value pushes the index up.
INDEX_DEF = {
    "digital_overload": {
        "daily_screen_time": +1, "social_media_hours": +1, "doomscrolling_duration": +1,
        "app_switch_frequency": +1, "notification_count": +1, "smartphone_unlocks": +1,
        "late_night_device_usage": +1,
    },
    "recovery_deficit": {
        "sleep_hours": -1, "sleep_quality": -1, "physical_activity": -1,
        "caffeine_intake": +1, "stress_level": +1,
    },
    "focus_capacity": {
        "deep_work_hours": +1, "focus_sessions": +1, "concentration_score": +1,
        "task_completion_rate": +1, "distraction_frequency": -1,
    },
    "psych_strain": {
        "mental_fatigue": +1, "emotional_exhaustion": +1,
        "motivation_level": -1, "work_satisfaction": -1,
    },
    "environment_quality": {"workspace_quality": +1, "internet_stability": +1},
}
INDEX_COLS = list(INDEX_DEF)
PROBLEM_SIGN = {
    "digital_overload": +1, "recovery_deficit": +1, "focus_capacity": -1,
    "psych_strain": +1, "environment_quality": -1,
}
INDEX_LABELS = {
    "digital_overload": "Digital overload",
    "recovery_deficit": "Poor recovery",
    "focus_capacity": "Focus capacity",
    "psych_strain": "Mental strain",
    "environment_quality": "Work environment",
}
PROBLEM_LABELS = {  # index read in the "higher = worse" direction
    "digital_overload": "Digital overload",
    "recovery_deficit": "Poor recovery",
    "focus_capacity": "Low focus",
    "psych_strain": "Mental strain",
    "environment_quality": "Poor environment",
}
PHRASE_PROBLEM = {
    "digital_overload": "heavy device use",
    "recovery_deficit": "poor recovery",
    "focus_capacity": "low focus",
    "psych_strain": "mental strain",
    "environment_quality": "poor work environment",
}
PHRASE_STRENGTH = {
    "digital_overload": "light device use",
    "recovery_deficit": "good recovery",
    "focus_capacity": "strong focus",
    "psych_strain": "low mental strain",
    "environment_quality": "good work environment",
}
INTERVENTIONS = {
    "digital_overload": [
        "Right-to-disconnect policy after hours; turn off non-urgent notifications",
        "Batch notifications into set times; fewer chat channels; coaching on digital habits",
    ],
    "recovery_deficit": [
        "Sleep and activity programme (step challenges, protected breaks)",
        "Limit after-hours work; stress-management support (EAP, mindfulness)",
    ],
    "focus_capacity": [
        "Protected deep-work blocks or meeting-free days; fewer context switches",
        "Training on prioritisation and time management; review the main sources of distraction",
    ],
    "psych_strain": [
        "Regular 1:1s with managers; review workload and how clear the goals are",
        "Recognition and development plans; access to counselling",
    ],
    "environment_quality": [
        "Upgrade equipment and workspace; home-office or internet allowance",
        "Faster IT support; minimum standards for remote setups",
    ],
}
MAINTAIN_ACTION = "Keep current practices; use as a comparison group and as peer mentors"
RISK_LEVELS = [  # (minimum risk score, label, status token used by the reports)
    (0.80, "Very high", "vhigh"),
    (0.30, "High", "high"),
    (-np.inf, "Low", "low"),
]
CROSS_CUTTING_PP = 5.0  # a warning sign whose rate differs < 5 pp across segments is organisation-wide
COMPANY_WIDE_ACTIONS = {
    "Sleep under 6 h": "Company-wide sleep health programme; no work messages after 9 pm",
    "High stress (8+)": "Employee assistance programme (EAP) and stress-management training at all levels",
    "Late-night device use": "Default do-not-disturb outside working hours in internal tools",
    "Screen time over 10 h": "Screen-break guidance (20-20-20 rule); screen-free meetings",
    "Deep work under 2 h": "Shared focus hours across the company (for example, no meetings 9-11 am)",
}
NAME_THRESHOLD = 0.30  # |SD| an index must reach before it names a segment


def build_indices(df: pd.DataFrame) -> pd.DataFrame:
    """z-score each column, apply its sign, average within the index, then re-standardise."""
    z = df[CLUSTER_FEATURES].astype("float32")
    z = (z - z.mean()) / z.std()
    out = {name: sum(sign * z[col] for col, sign in members.items()) / len(members)
           for name, members in INDEX_DEF.items()}
    idx = pd.DataFrame(out, index=df.index).astype("float32")
    return (idx - idx.mean()) / idx.std()


def eta_squared(values, labels) -> float:
    """Share of the outcome's variance explained by knowing the segment."""
    values = pd.Series(np.asarray(values))
    grand = values.mean()
    grp = values.groupby(np.asarray(labels))
    return float((grp.count() * (grp.mean() - grand) ** 2).sum() / ((values - grand) ** 2).sum())


def mean_pairwise_ari(labelings: list[np.ndarray]) -> tuple[float, float]:
    scores = [adjusted_rand_score(a, b) for a, b in itertools.combinations(labelings, 2)]
    return float(np.mean(scores)), float(np.min(scores))


def name_segment(problem_z: pd.Series) -> str:
    """Name a segment after its strongest problems, topped up with strengths."""
    problems = problem_z[problem_z >= NAME_THRESHOLD].sort_values(ascending=False)
    strengths = problem_z[problem_z <= -NAME_THRESHOLD].sort_values()
    parts = [PHRASE_PROBLEM[c] for c in problems.index[:2]]
    parts += [PHRASE_STRENGTH[c] for c in strengths.index[: 2 - len(parts)]]
    if not parts:
        return "Close to average"
    text = " + ".join(parts)
    return text[0].upper() + text[1:]


def risk_level(score: float) -> tuple[str, str]:
    for threshold, label, status in RISK_LEVELS:
        if score >= threshold:
            return label, status
    raise AssertionError("RISK_LEVELS must end with -inf")
