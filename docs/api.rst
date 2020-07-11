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
Survey API Client
*********************

The **Survey API Client** is the primary API client for interacting with the
**Dynata Survey Authoring** system's survey API.

.. module:: CmixAPIClient.api

.. autoclass:: CmixAPI
  :members:
