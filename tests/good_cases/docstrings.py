"""Demo for docstring handling.

It's interesting that a blank line is left after the docstring for classes but
not for functions.

"""


@public
class Template(string.Template):
    """Match any attribute path."""

    idpattern = r'[_a-z][_a-z0-9.]*'


def rand():
    """Example function."""
    return 0
