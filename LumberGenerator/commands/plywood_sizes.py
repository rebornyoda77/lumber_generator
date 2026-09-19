"""Nominal-to-actual thickness lookup table for sanded plywood panels.

Like dimensional lumber, sanded plywood's actual thickness runs slightly
under its nominal size. Actual values below follow the common
1/32in-under convention for sanded (A/B, BC, etc.) plywood. Extend this
table to add more nominal thicknesses - nothing else needs to change.
"""

# nominal thickness (as a fraction string) -> actual thickness in inches
NOMINAL_TO_ACTUAL_THICKNESS_IN = {
    "1/4": 0.219,
    "3/8": 0.344,
    "1/2": 0.469,
    "5/8": 0.594,
    "3/4": 0.719,
}

# Display order for the thickness dropdown.
NOMINAL_THICKNESS_ORDER = ["1/4", "3/8", "1/2", "5/8", "3/4"]


def get_actual_thickness_in(nominal_thickness: str) -> float:
    return NOMINAL_TO_ACTUAL_THICKNESS_IN[nominal_thickness]


def nominal_thickness_to_name_token(nominal_thickness: str) -> str:
    """Fraction strings like "3/4" aren't safe/readable in a component name,
    so turn "3/4" into "3-4in" for naming purposes.
    """
    return nominal_thickness.replace("/", "-") + "in"
