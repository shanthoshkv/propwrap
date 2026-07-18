"""propwrap — friendly propellant thermochemistry (RocketCEA / Cantera).

Quick start
-----------
>>> from propwrap import Mixture, compare_propellants, set_defaults
>>> m = Mixture("RP-1", "LOX")
>>> print(m.evaluate(of=2.56, pc=70, eps=20))  # no plot
>>> set_defaults(pc=70, eps=40)
>>> from propwrap import characterize
>>> characterize("CH4", "LOX", of=3.0, plot=False)
"""

from propwrap.blends import BlendComponent, add_blend, blend_card_summary
from propwrap.defaults import Case, get_defaults, reset_defaults, set_defaults
from propwrap.models import (
    CrossValidationResult,
    DensityIspCurve,
    DensityIspPoint,
    EngineCase,
    GammaProfile,
    MixtureStudy,
    PerformanceResult,
    StationState,
    SweepResult,
    TradeResult,
    TradeRow,
)
from propwrap.propellant import Mixture, Propellant, PropellantPair
from propwrap.propellant_library import add_custom_propellant, list_propellants
from propwrap.registry import (
    PropellantRecord,
    get_propellant,
    list_registry,
    register,
)
from propwrap.sanity import sanity_check
from propwrap.trades import density_isp_curve, trade_at_optimum_of
from propwrap import units
from propwrap.units import convert
from propwrap.workflows import (
    CharacterizeResult,
    characterize,
    compare_propellants,
    define_blend,
)

# Friendly aliases
lookup = get_propellant
compare_pairs = compare_propellants

__version__ = "0.1.0"

__all__ = [
    # primary
    "Mixture",
    "Propellant",
    "PropellantPair",
    "Case",
    "set_defaults",
    "get_defaults",
    "reset_defaults",
    # workflows
    "characterize",
    "compare_propellants",
    "compare_pairs",
    "define_blend",
    "CharacterizeResult",
    # registry
    "PropellantRecord",
    "lookup",
    "get_propellant",
    "list_registry",
    "list_propellants",
    "register",
    "add_blend",
    "BlendComponent",
    "blend_card_summary",
    "add_custom_propellant",
    # trades
    "density_isp_curve",
    "trade_at_optimum_of",
    # models
    "PerformanceResult",
    "StationState",
    "GammaProfile",
    "CrossValidationResult",
    "SweepResult",
    "MixtureStudy",
    "EngineCase",
    "DensityIspPoint",
    "DensityIspCurve",
    "TradeRow",
    "TradeResult",
    "sanity_check",
    "units",
    "convert",
    "__version__",
]
