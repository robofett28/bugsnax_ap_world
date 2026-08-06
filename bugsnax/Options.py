"""
Options.py - YAML options.
"""
from dataclasses import dataclass
from Options import Range, PerGameCommonOptions


class GoldenSnaxRequired(Range):
    """How many Golden Snax (MacGuffin Item) must be collected,
    on top of beating the game to reach the goal.
    Capped at 35.
    Setting to 0 will disable this requirement."""
    display_name = "Golden Snax Required"
    range_start = 1
    range_end = 50
    default = 20


class GoldenSnaxExtra(Range):
    """Extra Golden Snax placed in the pool ON TOP OF golden_snax_required,
    E.g. required=20, extra=5; places 25 Golden Snax total
    You only need to find 20 of them to goal.
    """
    display_name = "Extra Golden Snax"
    range_start = 0
    range_end = 49
    default = 5


@dataclass
class BugsnaxOptions(PerGameCommonOptions):
    golden_snax_required: GoldenSnaxRequired
    golden_snax_extra: GoldenSnaxExtra
