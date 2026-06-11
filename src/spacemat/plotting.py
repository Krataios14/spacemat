"""Ashby-style scatter plots. Needs the [plot] extra for matplotlib."""

from __future__ import annotations

from typing import Optional, Sequence

from .criteria import Property
from .db import load_all
from .schema import Material
from .units import as_kelvin

_CATEGORY_COLORS = {
    "metal": "#1f77b4",
    "polymer": "#2ca02c",
    "composite": "#9467bd",
    "adhesive": "#ff7f0e",
    "coating": "#8c564b",
    "elastomer": "#d62728",
    "lubricant": "#7f7f7f",
}


def ashby_plot(x: Property, y: Property,
               materials: Optional[Sequence[Material]] = None,
               T_service=None,
               logx: bool = False, logy: bool = False,
               ax=None):
    """Scatter materials on two property tokens; returns the Axes."""
    import matplotlib.pyplot as plt

    t_k = as_kelvin(T_service) if T_service is not None else None
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    seen_categories = set()
    for m in (materials if materials is not None else load_all()):
        xv = x.getter(m, t_k)
        yv = y.getter(m, t_k)
        if xv is None or yv is None:
            continue
        color = _CATEGORY_COLORS.get(m.category, "#333333")
        label = m.category if m.category not in seen_categories else None
        seen_categories.add(m.category)
        ax.scatter(xv, yv, s=60, color=color, label=label, zorder=3)
        ax.annotate(m.name, (xv, yv), textcoords="offset points",
                    xytext=(6, 4), fontsize=8)

    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel(x.label)
    ax.set_ylabel(y.label)
    title = f"{y.label} vs {x.label}"
    if t_k is not None:
        title += f" at {t_k:g} K"
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    if seen_categories:
        ax.legend(title="category", fontsize=8)
    return ax
