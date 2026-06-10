"""spacemat: programmatic access and screening for spaceflight materials data.

Quick start::

    from spacemat import screen, TML, CVCM, K
    passing = screen(TML < 1.0, CVCM < 0.1, T_service=90*K)
    for r in passing:
        print(r.material.name)
"""

from .criteria import (CVCM, DENSITY, THERMAL_CONDUCTIVITY, TML, ULTIMATE_STRENGTH, WVR,
                       YIELD_STRENGTH, Criterion, Property)
from .db import get, load_all
from .report import compliance_report
from .schema import Material, Outgassing, PropertyCurve
from .screen import ScreenResult, screen
from .units import K, Quantity, degC, degF

__version__ = "0.1.0"

__all__ = [
    "screen", "ScreenResult", "get", "load_all", "compliance_report",
    "Material", "Outgassing", "PropertyCurve", "Criterion", "Property",
    "TML", "CVCM", "WVR", "DENSITY", "YIELD_STRENGTH", "ULTIMATE_STRENGTH",
    "THERMAL_CONDUCTIVITY", "K", "degC", "degF", "Quantity", "ashby_plot",
]


def ashby_plot(*args, **kwargs):
    from .plotting import ashby_plot as _ashby
    return _ashby(*args, **kwargs)
