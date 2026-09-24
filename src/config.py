"""Shared paths, column groups, labels and loading helpers for the burnout/productivity analysis."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "archive (1)" / "digital_burnout_productivity_dataset_5M (1).csv"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
VISUALIZE = ROOT / "visualize"

for _d in (PROCESSED, REPORTS, VISUALIZE):
    _d.mkdir(parents=True, exist_ok=True)

CATEGORICAL = ["occupation", "work_mode", "device_usage_type", "mental_state", "productivity_category"]
OUTCOMES = ["burnout_risk", "productivity_score"]

FEATURE_GROUPS = {
    "Digital load": [
        "daily_screen_time",
        "social_media_hours",
        "doomscrolling_duration",
        "app_switch_frequency",
        "notification_count",
        "smartphone_unlocks",
        "late_night_device_usage",
    ],
    "Focus & output": [
        "focus_sessions",
        "deep_work_hours",
        "distraction_frequency",
        "task_completion_rate",
        "concentration_score",
        "meeting_hours",
    ],
    "Sleep & recovery": [
        "sleep_hours",
        "sleep_quality",
        "caffeine_intake",
        "physical_activity",
        "stress_level",
    ],
    "Work environment": [
        "workspace_quality",
        "internet_stability",
        "remote_work_days",
    ],
    "Mental state": [
        "motivation_level",
        "mental_fatigue",
        "emotional_exhaustion",
        "work_satisfaction",
    ],
}

CLUSTER_FEATURES = [c for cols in FEATURE_GROUPS.values() for c in cols]
NUMERIC = ["age"] + CLUSTER_FEATURES + OUTCOMES

# float32/int16/category keeps the 5M x 34 frame near 0.55 GB instead of ~2.6 GB.
DTYPES = {
    "user_id": "int32",
    "age": "int16",
    **{c: "category" for c in CATEGORICAL},
    **{c: "float32" for c in CLUSTER_FEATURES + OUTCOMES},
}

RANDOM_STATE = 42

LABELS = {
    "age": "Age",
    "daily_screen_time": "Screen time (h/day)",
    "social_media_hours": "Social media (h/day)",
    "doomscrolling_duration": "Doomscrolling (h/day)",
    "app_switch_frequency": "App switches per day",
    "notification_count": "Notifications per day",
    "smartphone_unlocks": "Phone unlocks per day",
    "late_night_device_usage": "Late-night device use (0/1)",
    "focus_sessions": "Focus sessions per day",
    "deep_work_hours": "Deep work (h/day)",
    "distraction_frequency": "Distractions per day",
    "task_completion_rate": "Task completion rate (%)",
    "concentration_score": "Concentration (1-10)",
    "meeting_hours": "Meetings (h/day)",
    "sleep_hours": "Sleep (h/night)",
    "sleep_quality": "Sleep quality (1-10)",
    "caffeine_intake": "Caffeine intake (per day, unit not stated)",
    "physical_activity": "Physical activity (h/day)",
    "stress_level": "Stress (1-10)",
    "workspace_quality": "Workspace quality (1-10)",
    "internet_stability": "Internet stability (1-10)",
    "remote_work_days": "Remote days per week",
    "motivation_level": "Motivation (1-10)",
    "mental_fatigue": "Mental fatigue (1-10)",
    "emotional_exhaustion": "Emotional exhaustion (1-10)",
    "work_satisfaction": "Job satisfaction (1-10)",
    "burnout_risk": "Burnout risk (0-100)",
    "productivity_score": "Productivity score (0-100)",
    "occupation": "Occupation",
    "work_mode": "Work mode",
    "device_usage_type": "Device use type",
    "mental_state": "Self-reported mental state",
    "productivity_category": "Productivity category",
}


def red_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean matrix of workplace warning signs; thresholds are the same everywhere in the project."""
    return pd.DataFrame(
        {
            "Late-night device use": df["late_night_device_usage"] == 1,
            "Sleep under 6 h": df["sleep_hours"] < 6,
            "High emotional exhaustion (8+)": df["emotional_exhaustion"] >= 8,
            "High mental fatigue (8+)": df["mental_fatigue"] >= 8,
            "High stress (8+)": df["stress_level"] >= 8,
            "Low job satisfaction (3 or less)": df["work_satisfaction"] <= 3,
            "Low motivation (3 or less)": df["motivation_level"] <= 3,
            "Deep work under 2 h": df["deep_work_hours"] < 2,
            "Screen time over 10 h": df["daily_screen_time"] > 10,
            "Burnout risk 70+": df["burnout_risk"] >= 70,
            "Low productivity category": df["productivity_category"] == "Low",
        },
        index=df.index,
    )


def load_raw(nrows: int | None = None) -> pd.DataFrame:
    """Read the raw CSV with memory-efficient dtypes."""
    return pd.read_csv(RAW_CSV, dtype=DTYPES, nrows=nrows)


def describe_memory(df: pd.DataFrame) -> str:
    return f"{df.memory_usage(deep=True).sum() / 1024**3:.2f} GB"
