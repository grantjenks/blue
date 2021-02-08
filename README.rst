====
Blue
====

Some folks like `black <https://black.readthedocs.io/en/stable/>`_ but I
prefer `blue <https://blue.readthedocs.io/en/latest/>`_.


What is blue?
=============

``blue`` is a somewhat less uncompromising code formatter than ``black``, the
OG of Python formatters.  We love the idea of automatically formatting Python
code, for the same reasons that inspired ``black``, however we take issue with
some of the decisions ``black`` makes.  Kudos to ``black`` for pioneering code
formatting for Python, and for its excellent implementation.

Where the ``blue`` maintainers disagree with the stylistic (and
unconfigurable) choices made by ``black``, we monkeypatch to change these
decisions to our own liking.  We intend for these differences to be minimal;
even in cases where we'd prefer something different, there's a lot we can live
with for the sake of consistency.

We'd prefer not to fork or monkeypatch.  Instead, our hope is that eventually
we'll be able to work with the ``black`` maintainers to add just a little bit
of configuration and merge back into the ``black`` project.  We'd be ecstatic
if ``blue`` eventually were retired.  Until then, we'll maintain our small set
of hacks on top of ``black`` and carefully consider what other deviations are
needed to assuage our sensitive, but experienced, eye.


How do I use blue?
==================

Exactly the same as you would use ``black``.  Invoke and configure ``blue`` as
you would ``black`` -- just replace the ``black`` command with ``blue``, sit
back, and enjoy even betterly formatted Python code!  You can refer to
`black's <https://black.readthedocs.io/en/stable/>`_ documentation for
anything not listed here.


So what's different?
====================

Here is a brief list of differences between ``blue`` and ``black``:

* ``blue`` defaults to single-quoted strings.  This is probably the most
  painful ``black`` choice to our eyes, and the thing that inspired ``blue``.
  We strongly prefer using single quoted strings over double quoted strings
  for everything *except* docstrings.  Don't ask us why we prefer double
  quoted strings for docstrings; it just looks better to us!  For all other
  strings, ``blue`` defaults to single quoted strings.

* ``blue`` defaults to line lengths of 79 characters. Nearly every project
  creates a pyproject.toml just to change this one setting so making it
  consistent with PEP 8 seems relatively harmless.

* ``blue`` preserves the whitespace before the hash mark for right hanging
  comments.

* ``blue`` supports multiple config files: ``pyproject.toml``, ``setup.cfg``,
  ``tox.ini``, and ``.blue``.

We are `accumulating <https://github.com/grantjenks/blue/issues/2>`_ a list of
other deviations we are considering.  As we decide to implement any particular
suggestion, we'll turn those into individual issues and tackle them
one-by-one.  If you have suggestions for other deviations from ``black``'s
choices, please open a separate ticket on our tracker, and we'll see how it
goes!


Why "blue"?
===========

Several reasons!  If your formatter is going to beat up your code, it'll leave
it black and blue, or maybe in this case, black *or* blue.  Blue is better!

We also thought about "tan" because, yum!  But that project name was already
taken.  Frankly, "blue" was also taken, but largely unused.  Our thanks to
Nick Ficano for donating the project namespace to us!

Blue is also the color of `LinkedIn <https://www.linkedin.com/>`_, the
authors' gracious employer, and we intend to socialize its use within our
company code base.


Contributors
============

``blue`` thanks this list of contributors for all its wonderful goodness.

* The `wonderful folks <https://github.com/psf/black#authors>`_ from the
  ``black`` project.
* Grant Jenks
* Barry Warsaw
* Corey from FutureSpaceDesigns for the unofficial logo and `blue project
  merchandise <https://www.teepublic.com/t-shirt/6556561-tobias-blue>`_.

``blue`` is licensed under the terms of the Apache License Version 2.0.
``black`` is `licensed <https://github.com/psf/black#license>`_ under the
terms of the MIT license.


Project details
===============

.. image:: https://img.shields.io/badge/code%20style-blue-blue.svg
   :target: https://blue.readthedocs.io/

.. image:: https://github.com/grantjenks/blue/workflows/integration/badge.svg
   :target: https://github.com/grantjenks/blue/actions?query=workflow%3Aintegration

.. image:: https://github.com/grantjenks/blue/workflows/release/badge.svg
   :target: https://github.com/grantjenks/blue/actions?query=workflow%3Arelease

* Project home: https://github.com/grantjenks/blue
* Report bugs and suggestions at: https://github.com/grantjenks/blue/issues
* Code hosting: https://github.com/grantjenks/blue.git
* Documentation: https://blue.readthedocs.io/en/latest
