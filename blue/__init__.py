"""Blue

Some folks like black but I prefer blue.

"""

import re

import black

from black import (
    Leaf,
    STRING_PREFIX_CHARS,
    is_multiline_string,
    prev_siblings_are,
    token,
    sub_twice,
    syms,
)

black_normalize_string_quotes = black.normalize_string_quotes


def is_docstring(leaf: Leaf) -> bool:
    # Most of this function was copied from Black!

    if not is_multiline_string(leaf):
        # For the purposes of docstring re-indentation, we don't need to do anything
        # with single-line docstrings.
        return False

    if prev_siblings_are(
        leaf.parent, [None, token.NEWLINE, token.INDENT, syms.simple_stmt]
    ):
        return True

    # Multiline docstring on the same line as the `def`.
    if prev_siblings_are(leaf.parent, [syms.parameters, token.COLON, syms.simple_stmt]):
        # `syms.parameters` is only used in funcdefs and async_funcdefs in the Python
        # grammar. We're safe to return True without further checks.
        return True

    if leaf.parent.prev_sibling is None:
        # Identify module docstrings.
        return True

    return False


def normalize_string_quotes(leaf: Leaf) -> None:
    """Prefer *single* quotes but only if it doesn't cause more escaping.

    Adds or removes backslashes as appropriate. Doesn't parse and fix
    strings nested in f-strings (yet).

    Note: Mutates its argument.
    """
    if is_docstring(leaf):
        black_normalize_string_quotes(leaf)
        return

    # The remainder of this function is copied from black but double quotes are
    # swapped with single quotes in all places.

    value = leaf.value.lstrip(STRING_PREFIX_CHARS)
    if value[:3] == "'''":
        return

    elif value[:3] == '"""':
        orig_quote = '"""'
        new_quote = "'''"
    elif value[0] == "'":
        orig_quote = "'"
        new_quote = '"'
    else:
        orig_quote = '"'
        new_quote = "'"
    first_quote_pos = leaf.value.find(orig_quote)
    if first_quote_pos == -1:
        return  # There's an internal error

    prefix = leaf.value[:first_quote_pos]
    unescaped_new_quote = re.compile(rf'(([^\\]|^)(\\\\)*){new_quote}')
    escaped_new_quote = re.compile(rf'([^\\]|^)\\((?:\\\\)*){new_quote}')
    escaped_orig_quote = re.compile(rf'([^\\]|^)\\((?:\\\\)*){orig_quote}')
    body = leaf.value[first_quote_pos + len(orig_quote) : -len(orig_quote)]
    if 'r' in prefix.casefold():
        if unescaped_new_quote.search(body):
            # There's at least one unescaped new_quote in this raw string
            # so converting is impossible
            return

        # Do not introduce or remove backslashes in raw strings
        new_body = body
    else:
        # remove unnecessary escapes
        new_body = sub_twice(escaped_new_quote, rf'\1\2{new_quote}', body)
        if body != new_body:
            # Consider the string without unnecessary escapes as the original
            body = new_body
            leaf.value = f'{prefix}{orig_quote}{body}{orig_quote}'
        new_body = sub_twice(escaped_orig_quote, rf'\1\2{orig_quote}', new_body)
        new_body = sub_twice(unescaped_new_quote, rf'\1\\{new_quote}', new_body)
    if 'f' in prefix.casefold():
        matches = re.findall(
            r'''
            (?:[^{]|^)\{  # start of the string or a non-{ followed by a single {
                ([^{].*?)  # contents of the brackets except if begins with {{
            \}(?:[^}]|$)  # A } followed by end of the string or a non-}
            ''',
            new_body,
            re.VERBOSE,
        )
        for m in matches:
            if '\\' in str(m):
                # Do not introduce backslashes in interpolated expressions
                return

    if new_quote == "'''" and new_body[-1:] == "'":
        # edge case:
        new_body = new_body[:-1] + "\\'"
    orig_escape_count = body.count('\\')
    new_escape_count = new_body.count('\\')
    if new_escape_count > orig_escape_count:
        return  # Do not introduce more escaping

    if new_escape_count == orig_escape_count and orig_quote == "'":
        return  # Prefer single quotes

    leaf.value = f'{prefix}{new_quote}{new_body}{new_quote}'


def monkey_patch_black():
    """Monkey patch black.

    Python, I love you.

    """
    black.normalize_string_quotes = normalize_string_quotes


def main():
    monkey_patch_black()
    black.main()


__title__ = 'blue'
__version__ = '0.4.0'
