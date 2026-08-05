"""Temporary speed-up logic for the long-press-right-arrow gesture.

The mapping (confirmed with the user) keeps the function continuous at the
boundaries:  x<=1 -> 3, 1<x<4 -> (5x+4)/3, 4<=x<=8 -> 2x, x>8 -> 16.
"""


def speed_for_turbo(x: float) -> float:
    if x <= 1:
        return 3.0
    if x < 4:
        return (5 * x + 4) / 3
    if x <= 8:
        return 2 * x
    return 16.0