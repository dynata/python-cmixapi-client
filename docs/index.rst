.. Dynata Survey Authoring (Cmix) Python Client documentation master file, created by
   sphinx-quickstart on Fri Jul 10 18:27:27 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. This documentation follows the Read The Docs documentation style guide which
   is maintained here:
   https://documentation-style-guide-sphinx.readthedocs.io/en/latest/style-guide.html

#################################################
Dynata Survey Authoring (Cmix) Python Client
#################################################

**Python library for programmatic interaction with the Dynata Survey Authoring
tool (Cmix)**

.. sidebar:: Version Compatibility

  The **Dynata Survey Authoring** client is designed to be compatible with
  Python 3.6 or higher.

.. toctree::
  :hidden:
  :maxdepth: 2
  :caption: Contents:

  Home <self>
  About Dynata Survey Authoring <about>
  Using the Client <using>
  The Survey Definition <survey_definition/index>
  Defining Survey Questions <survey_definition/questions>
  Managing Survey Logic <survey_definition/managing_logic>
  API Reference <api>
  Error Reference <errors>
  Contributor Guide <contributing>
  Testing Reference <testing>
  Release History <history>
  Glossary <glossary>

The **Dynata Survey Authoring Python Client** is a Python library that provides
Python bindings for the Dynata Survey Authoring API.

The library employs a standard and consistent syntax for easy use, and has been tested on
Python 3.6, 3.7, and 3.8.

.. contents::
  :depth: 3
  :backlinks: entry

***************
Installation
***************

To install the **Dynata Survey Authoring Python Client**, just execute:

.. code:: bash

  $ pip install python-cmixapi-client

Dependencies
==============

.. include:: _dependencies.rst

************************************
Hello, World and Standard Usage
************************************

Prerequisites
================

To use the **Dynata Survey Authoring Python Client** you first need to have
access to the Dynata Survey Authoring platform, and to have been granted API
credentials for programmatic use. If you need programmatic credentials, please
contact your Dynata account executive to discuss your needs.

Authentication
=================

For your Python application to interact with **Dynata Survey Authoring**, you
need to first authenticate against the platform:

.. code-block:: python

  from CmixAPIClient.api import CmixAPI

  # 1. Initialize an instance of the DSA Python library with your authentication
  #    credentials.
  cmix = CmixAPI(
    username="test_username",
    password="test_password",
    client_id="test_client_id",
    client_secret="test_client_secret"
  )

  # 2. Authenticate against the API.
  cmix.authenticate()

  # 3. Execute whatever API calls you need to execute.
  surveys = cmix.get_surveys('closed')

Retrieving Surveys
======================

.. code-block:: python

  # Retrieve surveys whose status is 'closed'.
  # Returns a JSON collection of survey objects as a Python dict
  surveys = cmix.get_surveys('closed')


*********************
Questions and Issues
*********************

You can ask questions and report issues on the project's
`Github Issues Page <https://github.com/dynata/python-cmixapi-client/issues>`_

*********************
Contributing
*********************

We welcome contributions and pull requests! For more information, please see the
:doc:`Contributor Guide <contributing>`. And thanks to all those who've already
contributed:

.. include:: _contributors.rst

*********************
Testing
*********************

We use `TravisCI <http://travisci.org>`_ for our build automation and
`ReadTheDocs <https://readthedocs.org>`_ for our documentation.

Detailed information about our test suite and how to run tests locally can be
found in our :doc:`Testing Reference <testing>`.

**********************
License
**********************

The **Dynata Survey Authoring Python Client** is made available on a **MIT License**.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
