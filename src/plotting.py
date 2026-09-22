"""Matplotlib style for the notebook figures: red and blue on white, same palette as the HTML report."""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

from config import VISUALIZE

FIGURES = VISUALIZE / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

SURFACE = "#ffffff"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e6e6e3"
AXIS = "#c3c2b7"
DEEMPH = "#c9c9c4"
BLUE = "#2a78d6"   # productivity, "better", the neutral accent
RED = "#e34948"    # burnout, "worse"
BETTER = "#1c5cab"
WORSE = "#c23b37"
DIV_MID = "#f3f3f1"
RISK = {"vhigh": "#8f2426", "high": "#e5605e", "low": "#2a78d6"}
SEQ_RAMP = ["#e8f1fc", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
            "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281"]

DIVERGING = LinearSegmentedColormap.from_list("better_worse", [BETTER, DIV_MID, WORSE])
SEQUENTIAL = ListedColormap(SEQ_RAMP, name="blue_seq")


def num(v: float, digits: int = 1, signed: bool = False, suffix: str = "") -> str:
    """Plain number label with a true minus sign and an optional explicit plus."""
    text = f"{abs(v):,.{digits}f}"
    if round(v, digits) == 0:
        sign = ""
    elif v < 0:
        sign = "−"
    else:
        sign = "+" if signed else ""
    return sign + text + suffix


def setup_style() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "font.size": 10,
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.unicode_minus": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 9,
    })


def text_on(hex_color: str) -> str:
    """White or ink, whichever reads on the given fill."""
    r, g, b = (int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return INK if 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] > 0.179 else "#ffffff"


def cmap_hex(cmap, t: float) -> str:
    r, g, b, _ = cmap(min(max(t, 0.0), 1.0))
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", pad_inches=0.25)
