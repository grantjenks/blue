.. include:: ../README.rst


Changes
=======


2022-05-02 (0.9.0)
------------------
- Fix test suite failures due to a confluence of problems (GH#74)
- Upgrade dependency on Black to 22.1.0 to support Python 3.10 (GH#67)
- Add link to demo site at https://iblueit.dev (GH#69)


2022-02-22 (0.8.0)
------------------
- Fix compatibility with flake8 v4 (GH#58)


2021-08-16 (0.7.0)
------------------

- Bump dependency on Black to 21.7b0
- Prefer double quotes for non-docstring triple quoted strings (GH#10)
- Add support for "py39" as target-version (GH#44)
- Docstrings now always use triple-double-quoted strings (GH#5)


2021-02-11 (0.6.0)
------------------

- Preserve the whitespace before the hash mark for right hanging comments.
  (GH#20)
- Support multiple config files: pyproject.toml, setup.cfg, tox.ini, and .blue
  (GH#30)
- Fixed ``blue --version`` (GH#32)
- Added tests!


2021-01-17 (0.5.2)
------------------

- Fix reference to blue.__title__ when building docs (GH#26)


2021-01-16 (0.5.1)
------------------

* Change --target-version help and default line length to 79 (GH#16)
* Monkeypatch Black's cache dir to avoid poisoning (GH#19)
* Monkeypatch pyproject.toml parsing to read "blue" section (GH#15)
* Add integration and release GitHub actions.
* Add LICENSE file with Apache 2 details.
* Pin the dependency version of ``black`` to 20.8b1 (GH#17)
* Monkeypatching of ``black`` now works for multiple files (GH#6)
* Improved heuristics for identifying module docstrings (GH#3)
* Use double quotes for function docstrings (GH#4)
