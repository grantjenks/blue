.. include:: ../README.rst


Changes
=======


2021-XX-XX (0.6.0)
------------------

- Preserve the whitespace before the hash mark for right hanging comments.
  (GH#20)


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
