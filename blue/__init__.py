"""Blue

Some folks like black but I prefer blue.

"""

import re

import black

from black import (
    Leaf,
    Path,
    ProtoComment,
    STANDALONE_COMMENT,
    STRING_PREFIX_CHARS,
    make_comment,
    prev_siblings_are,
    sub_twice,
    syms,
    token,
    toml,
    user_cache_dir,
)

from functools import lru_cache

from typing import Any, Dict, List

__version__ = '0.6.0'

black_normalize_string_quotes = black.normalize_string_quotes
black_format_file_in_place = black.format_file_in_place

# Try not to poison Black's cache directory.
black.CACHE_DIR = Path(user_cache_dir('blue', version=__version__))


def is_docstring(leaf: Leaf) -> bool:
    # Most of this function was copied from Black!

    if prev_siblings_are(
        leaf.parent, [None, token.NEWLINE, token.INDENT, syms.simple_stmt]
    ):
        return True

    # Multiline docstring on the same line as the `def`.
    if prev_siblings_are(
        leaf.parent, [syms.parameters, token.COLON, syms.simple_stmt]
    ):
        # `syms.parameters` is only used in funcdefs and async_funcdefs in the
        # Python grammar. We're safe to return True without further checks.
        return True

    if leaf.parent.prev_sibling is None and leaf.column == 0:
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
        new_body = sub_twice(
            escaped_orig_quote, rf'\1\2{orig_quote}', new_body
        )
        new_body = sub_twice(
            unescaped_new_quote, rf'\1\\{new_quote}', new_body
        )
    if 'f' in prefix.casefold():
        matches = re.findall(
            r'''
            (?:[^{]|^)\{  # start of the str or a non-{ followed by a single {
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


def format_file_in_place(*args, **kws):
    # Black does some clever aync/parallelization so apply some monkey patches
    # here too.  We figure this out by looking at what works when formatting a
    # single file vs multiple files.
    black.normalize_string_quotes = normalize_string_quotes
    black.list_comments = list_comments
    return black_format_file_in_place(*args, **kws)


def parse_pyproject_toml(path_config: str) -> Dict[str, Any]:
    """Parse a pyproject toml file, pulling out relevant parts for Blue

    If parsing fails, will raise a toml.TomlDecodeError

    """
    # Most of this function was copied from Black!
    pyproject_toml = toml.load(path_config)
    config = pyproject_toml.get('tool', {}).get('blue', {})
    return {
        k.replace('--', '').replace('-', '_'): v for k, v in config.items()
    }


# Like black's list_comments() but preserves whitespace leading up to the hash
# mark.  Because what we really need to do is restore the whitespace after the
# line.lstrip() statement, there really is no good way to more narrowly
# monkeypatch.  This would be a good hook to install.  See
# https://github.com/grantjenks/blue/issues/14
@lru_cache(maxsize=4096)
def list_comments(prefix: str, *, is_endmarker: bool) -> List[ProtoComment]:
    result: List[ProtoComment] = []
    if not prefix or "#" not in prefix:
        return result

    consumed = 0
    nlines = 0
    ignored_lines = 0
    for index, orig_line in enumerate(prefix.split("\n")):
        consumed += len(orig_line) + 1  # adding the length of the split '\n'
        line = orig_line.lstrip()
        if not line:
            nlines += 1
        if not line.startswith("#"):
            # Escaped newlines outside of a comment are not really newlines at
            # all. We treat a single-line comment following an escaped newline
            # as a simple trailing comment.
            if line.endswith("\\"):
                ignored_lines += 1
            continue

        if index == ignored_lines and not is_endmarker:
            comment_type = token.COMMENT  # simple trailing comment
        else:
            comment_type = STANDALONE_COMMENT
        # Restore the original whitespace, but only for hanging comments.  We
        # use a heuristic to figure out hanging comments since that information
        # isn't explicitly passed in here (no, `is_endmarker` doesn't tell us,
        # apparently).  Hanging comments seem to not have a newline in prefix.
        #
        # Note however that the whitespace() function in black will add back
        # two leading spaces (see DOUBLESPACE).  Rather than monkey patch the
        # entire function, let's just remove up to two spaces before the hash
        # character.
        if '\n' not in prefix:
            whitespace = orig_line[:-len(line)]
            if len(whitespace) >= 2:
                whitespace = whitespace[2:]
            comment = whitespace + make_comment(line)
        else:
            comment = make_comment(line)
        result.append(
            ProtoComment(
                type=comment_type, value=comment, newlines=nlines,
                consumed=consumed
            )
        )
        nlines = 0
    return result


def monkey_patch_black():
    """Monkey patch black.

    Python, I love you.

    """
    black.format_file_in_place = format_file_in_place
    black.normalize_string_quotes = normalize_string_quotes
    black.parse_pyproject_toml = parse_pyproject_toml
    # Change the default line length to 79 characters.
    line_length_param = black.main.params[1]
    assert line_length_param.name == 'line_length'
    line_length_param.default = 79
    # Change the target version help doc to mention "Blue", not "Black".
    target_version_param = black.main.params[2]
    assert target_version_param.name == 'target_version'
    target_version_param.help = target_version_param.help.replace(
        'Black', 'Blue'
    )


def main():
    monkey_patch_black()
    black.main()
