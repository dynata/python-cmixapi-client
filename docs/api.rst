#############################
API Reference
#############################

.. contents::
  :depth: 3
  :backlinks: entry

**************************************************
Instantiating the API Client and Authenticating
**************************************************

To execute requests against the **Dynata Survey Authoring** API, you must first
instantiate an API client. This is done by creating an instance of a
:class:`CmixAPI` object, and calling the
:meth:`.authenticate() <CmixAPI.authenticate>` method to authenticate against
the API.

For example:

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

-----------


*********************
Core API Client
*********************

.. _survey_api_client:

The **Core API Client** is the primary API client for interacting with the
**Dynata Survey Authoring** system's API.

.. module:: CmixAPIClient.api

.. autoclass:: CmixAPI
  :members:

------------------------

*****************************
Project API Client
*****************************

The **Project API Client** is the primary API client for interacting with
individual :term:`Project` configurations within the Dynata Survey Authoring
system.

.. note::

  As the documentation below makes clear, in order to instantiate and make use
  of the **Project API Client**, you have to first instantiate and authenticate
  a :ref:`Core API Client <survey_api_client>` instance.

.. module:: CmixAPIClient.project

.. autoclass:: CmixProject
  :members:
