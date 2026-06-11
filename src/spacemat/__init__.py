"""Spaceflight materials data: screen(TML < 1.0, CVCM < 0.1, T_service=90*K)."""

from . import export, outgassing, thermal
from .compare import compare
from .criteria import (CONTRACTION, CVCM, DENSITY, ELONGATION, THERMAL_CONDUCTIVITY, TML,
                       ULTIMATE_STRENGTH, WVR, YIELD_STRENGTH, Criterion, Property)
from .db import get, load_all
from .report import compliance_report
from .schema import Material, Outgassing, PropertyCurve
from .screen import ScreenResult, screen
from .units import K, Quantity, degC, degF

__version__ = "0.2.0"

__all__ = [
    "screen", "ScreenResult", "get", "load_all", "compliance_report", "outgassing",
    "Material", "Outgassing", "PropertyCurve", "Criterion", "Property",
    "TML", "CVCM", "WVR", "DENSITY", "YIELD_STRENGTH", "ULTIMATE_STRENGTH",
    "THERMAL_CONDUCTIVITY", "CONTRACTION", "ELONGATION", "thermal", "compare", "export",
    "K", "degC", "degF", "Quantity", "ashby_plot",
]


def ashby_plot(*args, **kwargs):
    from .plotting import ashby_plot as _ashby
    return _ashby(*args, **kwargs)
