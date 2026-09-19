"""Nominal-to-actual dimension lookup table for dressed (S4S) dimensional lumber.

Dimensions are actual, dressed sizes in inches: (thickness, width).
Extend this table to add more nominal sizes - nothing else needs to change.
"""

# nominal size -> (actual thickness in, actual width in)
NOMINAL_TO_ACTUAL_IN = {
    "1x2": (0.75, 1.5),
    "1x4": (0.75, 3.5),
    "1x6": (0.75, 5.5),
    "1x8": (0.75, 7.25),
    "2x4": (1.5, 3.5),
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
    "4x4": (3.5, 3.5),
}

# Display order for the size dropdown (dict order is otherwise insertion order,
# but this keeps the order intentional and independent of the table above).
NOMINAL_SIZE_ORDER = [
    "2x4",
    "2x6",
    "2x8",
    "2x10",
    "2x12",
    "4x4",
    "1x2",
    "1x4",
    "1x6",
    "1x8",
]


def get_actual_dimensions_in(nominal_size: str):
    """Return (thickness_in, width_in) actual dimensions for a nominal size string."""
    return NOMINAL_TO_ACTUAL_IN[nominal_size]
