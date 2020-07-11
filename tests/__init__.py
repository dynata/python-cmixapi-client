# -*- coding: utf-8 -*-

"""
************************
Testing Philosophy
************************

.. todo::

  Re-write this whole page to align the testing philosophy with the implementation
  of unit tests in the library.

.. note::

  Unit tests for the **Dynata Survey Authoring** library are written using
  :mod:`unittest <python:unittest>` and managed/executed using `pytest`_.

There are many schools of thought when it comes to test design. When building
the **Dynata Survey Authoring Python Library**, we decided to focus on
practicality. That means:

  * **DRY is good, KISS is better.** To avoid repetition, our test suite makes
    extensive use of fixtures, parametrization, and decorator-driven behavior.
    This minimizes the number of test functions that are nearly-identical.
    However, there are certain elements of code that are repeated in almost all test
    functions, as doing so will make future readability and maintenance of the
    test suite easier.
  * **Coverage matters...kind of.** We have documented the primary intended
    behavior of every function in the **Dynata Survey Authoring** library, and the
    most-likely failure modes that can be expected.  At the time of writing, we
    have about 85% code coverage. Yes, yes: We know that is less than 100%. But
    there are edge cases which are almost impossible to bring about, based on
    confluences of factors in the wide world. Our goal is to test the key
    functionality, and as bugs are uncovered to add to the test functions as
    necessary.

************************
Test Organization
************************

Each individual test module (e.g. ``test_modulename.py``) corresponds to a
conceptual grouping of functionality. For example:

* ``test_api.py`` tests API functions found in
  ``CmixAPIClient/api.py``

*****************
Linting
*****************

Linting software is strongly recommended to improve code quality and maintain
readability in Python projects. Python's official linting package is called
:doc:`pycodestyle <pycodestyle:index>`, but another useful linting package is called
:doc:`flake8 <flake8:index>`.

Flake8 runs three different linters on your code, including
:doc:`pycodestyle <pycodestyle:index>` and a package called
`PyFlakes <https://github.com/PyCQA/pyflakes>`_ that checks for things like
unused imports.

To lint the files:

.. code-block:: bash

  python-cmixapi-client/ $ flake8 .


**************************************
Configuring & Running Tests
**************************************

Configuration Files
======================

To support the automated execution of the library's test suite, we have prepared
a ``pytest.ini`` file that is used to establish environment variables for test
purposes.

Default linting configuration is managed through both ``.flake8`` and
``pytcodestyle`` configuration files.

Running Tests
==============

Linting the Library
-----------------------

.. code-block:: bash

  python-cmixapi-client/ $ flake8 .


Entire Test Suite
---------------------

.. code-block:: bash

  tests/ $ pytest

Testing a Module
--------------------

.. code-block:: bash

  tests/ $ pytest tests/test_module.py

Testing a Function
----------------------

.. code-block:: bash

  tests/ $ pytest tests/test_module.py -k 'test_my_test_function'

.. target-notes::

.. _`pytest`: https://docs.pytest.org/en/latest/
.. _`tox`: https://tox.readthedocs.io
.. _`mocks`: https://en.wikipedia.org/wiki/Mock_object
.. _`stubs`: https://en.wikipedia.org/wiki/Test_stub
"""
