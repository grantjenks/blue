"""Blue

Some folks like black but I prefer blue.
"""

import logging
import re
import sys

from importlib import machinery

__version__ = '0.9.1'


# Black 1.0+ ships pre-compiled libraries with mypyc, which we can't
# monkeypatch like needed. In order to ensure that the original .py files get
# loaded instead, we create a custom FileFinder that excludes the
# ExtensionFileLoader, then use that as the file finder for Black's modules.
# However, we should perform this run time check to ensure we're not running
# in an environment we can't support.

if 'black' in sys.modules and sys.modules['black'].__file__.endswith('.so'):
    raise RuntimeError(
        'A mypyc-compiled version of black has already been imported. '
        'This prevents blue from operating properly.'
    )


class NoMypycBlackFileFinder(machinery.FileFinder):
    def __init__(self, path: str, *loader_details) -> None:
        super().__init__(path, *loader_details)

        for hook in sys.path_hooks[1:]:
            try:
                self.original_finder = hook(path)
            except ImportError:
                continue
            else:
                break
        else:
            raise ImportError('Failed to find original import finder')

    def find_spec(self, fullname, *args, **kw):
        if fullname == 'black' or fullname.startswith('black.'):
            return super(NoMypycBlackFileFinder, self).find_spec(
                fullname, *args, **kw
            )
        else:
            return self.original_finder.find_spec(fullname, *args, **kw)

    @classmethod
    def path_hook(cls):
        return super(NoMypycBlackFileFinder, cls).path_hook(
            (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES),
            (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES),
        )


sys.path_hooks.insert(0, NoMypycBlackFileFinder.path_hook())
sys.path_importer_cache.clear()


# These have to be imported after the import system hackery above, so we just
# ignore the E402 warning from flake8.
import black
import black.cache
import black.comments
import black.strings

from black import Leaf, Path, click, token
from black.cache import user_cache_dir
from black.comments import ProtoComment, make_comment
from black.files import tomli
from black.linegen import LineGenerator as BlackLineGenerator
from black.lines import Line
from black.nodes import (
    STANDALONE_COMMENT,
    is_multiline_string,
    prev_siblings_are,
    syms,
)
from black.strings import (
    STRING_PREFIX_CHARS,
    get_string_prefix,
    normalize_string_prefix,
    sub_twice,
)

from flake8.options import config as flake8_config
from flake8.options import manager as flake8_manager

from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Iterator, List, Optional, Pattern

from click.decorators import version_option


LOG = logging.getLogger(__name__)

black_format_file_in_place = black.format_file_in_place
black_strings_fix_docstring = black.strings.fix_docstring
black_strings_normalize_string_quotes = black.strings.normalize_string_quotes

# Try not to poison Black's cache directory.
black.cache.CACHE_DIR = Path(user_cache_dir('blue', version=__version__))


# Blue works by monkey patching black, so we don't have to duplicate
# everything, and we can take advantage of black's excellent implementation.
# We still have to monkey patch more than we want so eventually, these ought
# to be implemented by hooks in black that we can set.  Until then, there are
# essentially two modes of black operation we have to deal with.
#
# When black is formatting a single file, it's easy to monkey patch at an entry
# point for blue.  But when formatting multiple files, black uses some clever
# asynchronous parallelization which prevents us from monkey patching a few
# things in the blue entry point.  By way of code inspection and
# experimentation, we've found a convenient place to monkey patch a few things
# after the subprocesses have been spawned.  Define your monkey patch points
# here.


class Mode(Enum):
    asynchronous = 1
    synchronous = 2


BLUE_MONKEYPATCHES = [
    # Synchronous Monkees.
    (black, 'format_file_in_place', Mode.synchronous),
    (black, 'parse_pyproject_toml', Mode.synchronous),
    (black, 'LineGenerator', Mode.synchronous),
    (black.files, 'parse_pyproject_toml', Mode.synchronous),
    (black.linegen, 'normalize_string_quotes', Mode.synchronous),
    (black.strings, 'normalize_string_quotes', Mode.synchronous),
    (black.trans, 'normalize_string_quotes', Mode.synchronous),
    (black.comments, 'list_comments', Mode.synchronous),
    (black.linegen, 'list_comments', Mode.synchronous),
    # Asynchronous Monkees.
    (black, 'LineGenerator', Mode.asynchronous),
    (black.linegen, 'normalize_string_quotes', Mode.asynchronous),
    (black.strings, 'normalize_string_quotes', Mode.asynchronous),
    (black.trans, 'normalize_string_quotes', Mode.asynchronous),
    (black.comments, 'list_comments', Mode.asynchronous),
    (black.linegen, 'list_comments', Mode.asynchronous),
]


def monkey_patch_black(mode: Mode) -> None:
    blue = sys.modules['blue']
    for module, function_name, monkey_mode in BLUE_MONKEYPATCHES:
        if monkey_mode is mode:
            setattr(module, function_name, getattr(blue, function_name))


# Because blue makes different choices than black, and all of this code is
# essentially ripped off from black, applying blue to it will change the
# formatting.  That will make diff'ing with black more difficult, so just turn
# off formatting for anything that comes from black.

# fmt: off
def is_docstring(leaf: Leaf) -> bool:
    if prev_siblings_are(
        leaf.parent, [None, token.NEWLINE, token.INDENT, syms.simple_stmt]
    ):
        return True

    # Multiline docstring on the same line as the `def`.
    if prev_siblings_are(leaf.parent, [syms.parameters, token.COLON, syms.simple_stmt]):
        # `syms.parameters` is only used in funcdefs and async_funcdefs in the Python
        # grammar. We're safe to return True without further checks.
        return True

    if leaf.parent.prev_sibling is None and leaf.column == 0:
        # Identify module docstrings.
        return True

    return False


# Re(gex) does actually cache patterns internally but this still improves
# performance on a long list literal of strings by 5-9% since lru_cache's
# caching overhead is much lower.
@lru_cache(maxsize=64)
def _cached_compile(pattern: str) -> Pattern[str]:
    return re.compile(pattern)


def normalize_string_quotes(s: str) -> str:
    """Prefer *single* quotes but only if it doesn't cause more escaping.

    Adds or removes backslashes as appropriate. Doesn't parse and fix
    strings nested in f-strings.
    """
    value = s.lstrip(STRING_PREFIX_CHARS)
    if value[:3] == '"""':
        return s

    elif value[:3] == "'''":
        orig_quote = "'''"
        new_quote = '"""'
    elif value[0] == "'":
        orig_quote = "'"
        new_quote = '"'
    else:
        orig_quote = '"'
        new_quote = "'"
    first_quote_pos = s.find(orig_quote)
    if first_quote_pos == -1:
        return s  # There's an internal error

    prefix = s[:first_quote_pos]
    unescaped_new_quote = _cached_compile(rf'(([^\\]|^)(\\\\)*){new_quote}')
    escaped_new_quote = _cached_compile(rf'([^\\]|^)\\((?:\\\\)*){new_quote}')
    escaped_orig_quote = _cached_compile(rf'([^\\]|^)\\((?:\\\\)*){orig_quote}')
    body = s[first_quote_pos + len(orig_quote) : -len(orig_quote)]
    if 'r' in prefix.casefold():
        if unescaped_new_quote.search(body):
            # There's at least one unescaped new_quote in this raw string
            # so converting is impossible
            return s

        # Do not introduce or remove backslashes in raw strings
        new_body = body
    else:
        # remove unnecessary escapes
        new_body = sub_twice(escaped_new_quote, rf'\1\2{new_quote}', body)
        if body != new_body:
            # Consider the string without unnecessary escapes as the original
            body = new_body
            s = f'{prefix}{orig_quote}{body}{orig_quote}'
        new_body = sub_twice(escaped_orig_quote, rf'\1\2{orig_quote}', new_body)
        new_body = sub_twice(unescaped_new_quote, rf'\1\\{new_quote}', new_body)
    if 'f' in prefix.casefold():
        matches = re.findall(
            r"""
            (?:(?<!\{)|^)\{  # start of the string or a non-{ followed by a single {
                ([^{].*?)  # contents of the brackets except if begins with {{
            \}(?:(?!\})|$)  # A } followed by end of the string or a non-}
            """,
            new_body,
            re.VERBOSE,
        )
        for m in matches:
            if '\\' in str(m):
                # Do not introduce backslashes in interpolated expressions
                return s

    if new_quote == "'''" and new_body[-1:] == "'":
        # edge case:
        new_body = new_body[:-1] + "\\'"
    orig_escape_count = body.count('\\')
    new_escape_count = new_body.count('\\')
    if new_escape_count > orig_escape_count:
        return s  # Do not introduce more escaping

    if new_escape_count == orig_escape_count and orig_quote == "'":
        return s  # Prefer double quotes

    return f'{prefix}{new_quote}{new_body}{new_quote}'


# Like black's list_comments() but preserves whitespace leading up to the hash
# mark.  Because what we really need to do is restore the whitespace after the
# line.lstrip() statement, there really is no good way to more narrowly
# monkeypatch.  This would be a good hook to install.  See
# https://github.com/grantjenks/blue/issues/14
@lru_cache(maxsize=4096)
def list_comments(prefix: str, *, is_endmarker: bool) -> List[ProtoComment]:
    """Return a list of :class:`ProtoComment` objects parsed from the given `prefix`."""
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


def parse_pyproject_toml(path_config: str) -> Dict[str, Any]:
    """Parse a pyproject toml file, pulling out relevant parts for Black

    If parsing fails, will raise a tomli.TOMLDecodeError
    """
    with open(path_config, "rb") as f:
        pyproject_toml = tomli.load(f)
    config = pyproject_toml.get("tool", {}).get("blue", {})
    return {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}


def fix_docstring(docstring: str, prefix: str) -> str:
    new_docstring = black_strings_fix_docstring(docstring, prefix)
    # Needs special handling for module docstring case!
    if docstring.endswith('\n') and not new_docstring.endswith('\n'):
        new_docstring += '\n'
    return new_docstring


class LineGenerator(BlackLineGenerator):

    def visit_STRING(self, leaf: Leaf) -> Iterator[Line]:
        if is_docstring(leaf) and "\\\n" not in leaf.value:
            # We're ignoring docstrings with backslash newline escapes because changing
            # indentation of those changes the AST representation of the code.
            docstring = normalize_string_prefix(leaf.value)
            prefix = get_string_prefix(docstring)
            docstring = docstring[len(prefix) :]  # Remove the prefix
            quote_char = docstring[0]
            # A natural way to remove the outer quotes is to do:
            #   docstring = docstring.strip(quote_char)
            # but that breaks on """""x""" (which is '""x').
            # So we actually need to remove the first character and the next two
            # characters but only if they are the same as the first.
            quote_len = 1 if docstring[1] != quote_char else 3
            docstring = docstring[quote_len:-quote_len]
            docstring_started_empty = not docstring

            if is_multiline_string(leaf):
                indent = " " * 4 * self.current_line.depth
                docstring = fix_docstring(docstring, indent)
            else:
                docstring = docstring.strip()

            if docstring:
                # Add some padding if the docstring starts / ends with a quote mark.
                if docstring[0] == quote_char:
                    docstring = " " + docstring
                if docstring[-1] == quote_char:
                    docstring += " "
                if docstring[-1] == "\\":
                    backslash_count = len(docstring) - len(docstring.rstrip("\\"))
                    if backslash_count % 2:
                        # Odd number of tailing backslashes, add some padding to
                        # avoid escaping the closing string quote.
                        docstring += " "
            elif not docstring_started_empty:
                docstring = " "

            # Enforce triple double quotes at this point.
            quote = '"""'
            leaf.value = prefix + quote + docstring + quote

        yield from self.visit_default(leaf)
# fmt: on


def format_file_in_place(*args, **kws):
    # This is a convenient place to monkey patch any function that must be
    # done after black's asynchronous invocation.
    monkey_patch_black(Mode.asynchronous)
    return black_format_file_in_place(*args, **kws)


try:
    BaseConfigParser = flake8_config.ConfigParser              # flake8 v4
except AttributeError:
    BaseConfigParser = flake8_config.MergedConfigParser        # flake8 v3


class MergedConfigParser(BaseConfigParser):
    def _parse_config(self, config_parser, parent=None):
        """Skip option parsing in flake8's config parsing."""
        config_dict = {}
        for option_name in config_parser.options(self.program_name):
            value = config_parser.get(self.program_name, option_name)
            LOG.debug('Option "%s" has value: %r', option_name, value)
            config_dict[option_name] = value
        return config_dict


def read_configs(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    """Read configs through the config param's callback hook."""
    # Use black's `read_pyproject_toml` for the default
    result = black.read_pyproject_toml(ctx, param, value)
    # Use flake8's config file parsing to load setup.cfg, tox.ini, and .blue
    # The parsing looks both in the project and user directories.
    finder = flake8_config.ConfigFileFinder('blue')
    manager = flake8_manager.OptionManager('blue', '0')
    parser = MergedConfigParser(manager, finder)
    config = parser.parse()
    # Merge the configs into Click's `default_map`.
    default_map: Dict[str, Any] = {}
    default_map.update(ctx.default_map or {})
    for key, value in config.items():
        key = key.replace('--', '').replace('-', '_')
        default_map[key] = value
    ctx.default_map = default_map
    return result


def main():
    monkey_patch_black(Mode.synchronous)
    # Reach in and monkey patch the Click options. This is tricky based on the
    # way Click works! This is highly fragile because the index into the Click
    # parameters is dependent on the decorator order for Black's main().
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
    # Change the config param callback to support setup.cfg, tox.ini, etc.
    config_param = black.main.params[25]
    assert config_param.name == 'config'
    config_param.callback = read_configs
    # Change the version string by adding a redundant Click `version_option`
    # decorator on `black.main`. Fortunately the added `version_option` takes
    # precedence over the existing one.
    version_string = f'{__version__}, based on black {black.__version__}'
    version_option(version_string)(black.main)
    black.main()
