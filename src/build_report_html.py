"""Build the self-contained interactive report visualize/report.html.

All 5M rows are folded into one cube (segment x occupation x work mode = 126 cells). Each cell keeps
the sums needed to recompute means, standard deviations, Pearson correlations, warning-sign rates
and the burnout x productivity density *exactly* for any filter combination in the browser.

Run after the notebook:           python src/build_report_html.py
Template-only change (fast path): python src/build_report_html.py --reuse
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

from config import FEATURE_GROUPS, LABELS, NUMERIC, OUTCOMES, PROCESSED, RAW_CSV, REPORTS, ROOT, VISUALIZE, red_flags
from segmentation import INDEX_DEF, PROBLEM_SIGN, build_indices

TEMPLATE = ROOT / "src" / "report_template.html"
OUTPUT = VISUALIZE / "report.html"
CACHE = PROCESSED / "report_data.json"
OUTCOME_BINS = 20  # 5-point bins on the 0-100 outcome scales


def sig(values, digits: int = 8) -> list:
    """Round to significant digits so the embedded JSON stays small without losing precision."""
    arr = np.asarray(values, dtype=float)
    return [None if np.isnan(v) else float(f"{v:.{digits}g}") for v in arr.ravel()]


def driver_direction() -> dict[str, int]:
    """+1 when a higher raw value is a problem, -1 when it is a strength, 0 when neutral."""
    out = {}
    for idx, members in INDEX_DEF.items():
        for col, sign in members.items():
            out[col] = sign * PROBLEM_SIGN[idx]
    return out


def render(payload: str) -> None:
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/{}", payload)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Saved -> {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024 ** 2:,.2f} MB)")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--reuse" in sys.argv and CACHE.exists():
        render(CACHE.read_text(encoding="utf-8"))
        return
    t0 = time.perf_counter()
    df = pd.read_parquet(PROCESSED / "employees.parquet")
    seg = pd.read_parquet(PROCESSED / "segment_assignment.parquet")
    assert len(seg) == len(df) and (seg["user_id"].to_numpy() == df["user_id"].to_numpy()).all(), \
        "segment_assignment.parquet does not match employees.parquet - re-run the notebook"
    meta_seg = json.loads((REPORTS / "segment_meta.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(df):,} rows ({time.perf_counter() - t0:,.1f}s)")

    occ_levels = list(df["occupation"].cat.categories)
    wm_levels = list(df["work_mode"].cat.categories)
    n_seg, n_occ, n_wm = int(meta_seg["k"]), len(occ_levels), len(wm_levels)
    n_cells = n_seg * n_occ * n_wm
    cell = (seg["segment_id"].to_numpy().astype(np.int64) * (n_occ * n_wm)
            + df["occupation"].cat.codes.to_numpy().astype(np.int64) * n_wm
            + df["work_mode"].cat.codes.to_numpy().astype(np.int64))
    keys = [[s, o, w] for s in range(n_seg) for o in range(n_occ) for w in range(n_wm)]

    def per_cell(weights=None) -> np.ndarray:
        return np.bincount(cell, weights=weights, minlength=n_cells)

    cells: dict[str, list] = {"key": keys, "n": per_cell().astype(int).tolist()}

    # raw (non-imputed) moments, centred on the global mean to avoid cancellation
    V = len(NUMERIC)
    mu_raw = df[NUMERIC].mean().to_numpy(dtype=float)
    cnt, s1, s2 = (np.zeros((n_cells, V)) for _ in range(3))
    for j, col in enumerate(NUMERIC):
        x = df[col].to_numpy(dtype=float)
        ok = ~np.isnan(x)
        xc = np.where(ok, x - mu_raw[j], 0.0)
        cnt[:, j] = per_cell(ok.astype(float))
        s1[:, j] = per_cell(xc)
        s2[:, j] = per_cell(xc * xc)
    cells.update({"cnt": cnt.astype(int).tolist(), "s1": [sig(r) for r in s1], "s2": [sig(r) for r in s2]})
    var_meta = [{"key": c, "label": LABELS[c],
                 "group": next((g for g, cols in FEATURE_GROUPS.items() if c in cols),
                               "Outcome" if c in OUTCOMES else "Profile")} for c in NUMERIC]
    print(f"Means and standard deviations ({time.perf_counter() - t0:,.1f}s)")

    # cross-products on median-imputed values -> exact Pearson r for any filter slice
    imp = df[NUMERIC].fillna(df[NUMERIC].median()).to_numpy(dtype=float)
    mu_imp = imp.mean(axis=0)
    imp -= mu_imp
    xs = np.stack([per_cell(imp[:, j]) for j in range(V)], axis=1)
    pairs = [(i, j) for i in range(V) for j in range(i, V)]
    xp = np.stack([per_cell(imp[:, i] * imp[:, j]) for i, j in pairs], axis=1)
    del imp
    cells.update({"xs": [sig(r) for r in xs], "xp": [sig(r) for r in xp]})
    print(f"Correlations ({len(pairs)} pairs) ({time.perf_counter() - t0:,.1f}s)")

    flags = red_flags(df)
    cells["flags"] = np.stack([per_cell(flags[c].to_numpy(dtype=float)) for c in flags.columns], axis=1).astype(int).tolist()
    nfl = flags.sum(axis=1).to_numpy()
    n_flag_bins = len(flags.columns) + 1
    cells["nfl"] = np.bincount(cell * n_flag_bins + nfl, minlength=n_cells * n_flag_bins).reshape(n_cells, -1).tolist()

    work = df.copy()
    feat = [c for cols in FEATURE_GROUPS.values() for c in cols]
    work[feat] = work[feat].fillna(work[feat].median())
    idx = build_indices(work)
    del work
    cells["idx"] = [sig(r, 7) for r in np.stack(
        [per_cell(idx[c].to_numpy(dtype=float) * PROBLEM_SIGN[c]) for c in meta_seg["index_cols"]], axis=1)]

    bb = np.clip((df["burnout_risk"].to_numpy() // (100 / OUTCOME_BINS)).astype(np.int64), 0, OUTCOME_BINS - 1)
    pb = np.clip((df["productivity_score"].to_numpy() // (100 / OUTCOME_BINS)).astype(np.int64), 0, OUTCOME_BINS - 1)
    o2 = np.bincount((cell * OUTCOME_BINS + bb) * OUTCOME_BINS + pb, minlength=n_cells * OUTCOME_BINS ** 2)
    cells["o2"] = o2.reshape(n_cells, -1).tolist()
    print(f"Warning signs, scores, outcome map ({time.perf_counter() - t0:,.1f}s)")

    data = {
        "meta": {
            "n_rows": int(len(df)), "file_name": RAW_CSV.name,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "outcome_bins": OUTCOME_BINS,
        },
        "vars": var_meta,
        "driver_dir": driver_direction(),
        "dims": {"segment": n_seg, "occupation": occ_levels, "work_mode": wm_levels},
        "flags": list(flags.columns),
        "mu_raw": sig(mu_raw),
        "cells": cells,
        "seg": meta_seg,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    CACHE.write_text(payload, encoding="utf-8")
    render(payload)
    print(f"Total {time.perf_counter() - t0:,.1f}s")


if __name__ == "__main__":
    main()
