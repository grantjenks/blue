"""Demo for formatting slices.

"""

import random


def first_5(values):
    return values[:5]


def last_5(values):
    return values[-5:]


def test_from_to(values, lo, hi):
    return values[lo:hi]


def test_expr_rhs(values):
    return values[: random.randrange(10)]


def test_expr_lhs(values):
    return values[random.randrange(10) :]


def test_expr_both(values):
    return values[random.randrange(10) : random.randrange(10, 20)]
