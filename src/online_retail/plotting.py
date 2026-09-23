"""Shared chart style so every figure in the project looks consistent."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from online_retail.data import PROJECT_ROOT

FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

PRIMARY = "#2a78d6"  # the measure being discussed
MUTED = "#c9c7c1"  # context, excluded or caveated values
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e5e1"


def set_style() -> None:
    """Apply a clean, low-ink matplotlib style."""
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlecolor": TEXT,
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "font.size": 10,
            "legend.frameon": False,
        }
    )


def format_gbp(value: float, _position: int | None = None) -> str:
    """Compact pound formatting for axes and labels: £1.2M, £350k, £90."""
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:.0f}k"
    return f"£{value:.0f}"


gbp_axis_formatter = FuncFormatter(format_gbp)


def plot_ranked_bars(
    ax: plt.Axes,
    values: pd.Series,
    title: str,
    xlabel: str,
    colors: list[str] | None = None,
    formatter=format_gbp,
) -> plt.Axes:
    """Horizontal bar chart, largest value on top, with a value label on each bar."""
    ordered = values.iloc[::-1]
    labels = [str(label) for label in ordered.index]
    bar_colors = colors[::-1] if colors else PRIMARY
    bars = ax.barh(labels, ordered.to_numpy(), color=bar_colors, height=0.65)

    ax.bar_label(
        bars, labels=[formatter(v) for v in ordered], padding=4, color=TEXT_SECONDARY, fontsize=9
    )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.margins(x=0.12)
    return ax


def save_figure(fig: plt.Figure, name: str) -> Path:
    """Save a figure under reports/figures so the README can display it."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path)
    return path
