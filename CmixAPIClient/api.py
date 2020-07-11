# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import logging

from .error import CmixError

log = logging.getLogger(__name__)

CMIX_SERVICES = {
    'auth': {
        'BASE_URL': 'https://auth.cmix.com',
        'TEST_URL': 'https://kaleidoscope-auth.cmix.com',
    },
    'file': {
        'BASE_URL': 'https://file-processing.cmix.com',
        'TEST_URL': 'https://kaleidoscope-file-processing.cmix.com',
    },
    'launchpad': {
        'BASE_URL': 'https://launchpad.cmix.com',
        'TEST_URL': 'https://kaleidoscope-launchpad.cmix.com',
    },
    'reporting': {
        'BASE_URL': 'https://reporting-api.cmix.com',
        'TEST_URL': 'https://kaleidoscope-reporting-api.cmix.com',
    },
    'survey': {
        'BASE_URL': 'https://survey-api.cmix.com',
        'TEST_URL': 'https://kaleidoscope-survey-api.cmix.com',
    },
    'test': {
        'BASE_URL': 'https://test.cmix.com',
        'TEST_URL': 'https://kaleidoscope-test.cmix.com',
    },
}

DEFAULT_API_TIMEOUT = 16

# - it seems like this class would work better as a singleton - and
#   maybe the method above (default_cmix_api) could create the singleton,
#   authenticate it, then return it - and all subsequent calls to
#   default_cmix_api would return the same authenticated singleton - no need
#   to keep authenticating on every request
# - default_cmix_api could also check_auth_headers before returning the
#   singleton - if it's not authenticated it could try authenticating or
#   creating a new instance THEN authenticating


class CmixAPI(object):
    """Base class that is used to provide API bindings for the
    **Dynata Survey Authoring (Cmix)** tool.

    To execute calls against the Dynata Survey Authoring API, instantiate this
    class, authenticate against the API, and leverage its methods to execute
    the applicable API calls.

    """
    # valid survey statuses
    SURVEY_STATUS_DESIGN = 'DESIGN'
    SURVEY_STATUS_LIVE = 'LIVE'
    SURVEY_STATUS_CLOSED = 'CLOSED'

    # valid extra survey url params
    SURVEY_PARAMS_STATUS_AFTER = 'statusAfter'

    def __init__(
            self,
            username = None,
            password = None,
            client_id = None,
            client_secret = None,
            test = False,
            timeout = None,
            *args,
            **kwargs
    ):
        """Construct a new ``CmixAPI`` object which represents the API client.

        :param username: The username used to authenticate against the API. Defaults
          to :obj:`None <python:None>`, but is required and will raise an exception
          if missing.
        :type username: :class:`str <python:str>`

        :param password: The password used to authenticate against the API. Defaults
          to :obj:`None <python:None>`, but is required and will raise an exception
          if missing.
        :type password: :class:`str <python:str>`

        :param client_id: The unique Client ID that is included in your API
          credentials. Defaults to :obj:`None <python:None>`, but is required and
          will raise an exception if missing.

          .. warning::

            If you do not have a Client ID, but intend to use the API, please
            contact your Dynata account executive.

        :type client_id: :class:`str <python:str>`

        :param client_secret: The Client Secret that is included in your API
          credentials. Defaults to :obj:`None <python:None>`, but is required and
          will raise an exception if missing.

          .. warning::

            If you do not have a Client ID, but intend to use the API, please
            contact your Dynata account executive.

        :type client_secret: :class:`str <python:str>`

        :param test: Flag which if ``True`` indicates that the instantiated client
          is intended to execute test requests, not actual requests. Defaults to
          ``False``.
        :type test: :class:`bool <python:bool>`

        :param timeout: The amount of time to wait before raising a timeout error.
          Defaults to 16 seconds.
        :type timeout: :class:`int <python:int>`

        :raises CmixError: If any authentication details (``username``, ``password``,
          ``client_id``, or ``client_secret``) are not supplied.

        """
        if None in [username, password, client_id, client_secret]:
            raise CmixError("All authentication data is required.")

        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret

        self.url_type = 'BASE_URL'
        if test is True:
            self.url_type = 'TEST_URL'

        self.timeout = timeout if timeout is not None else DEFAULT_API_TIMEOUT

    def check_auth_headers(self):
        """Validate that the API instance has been authenticated using
        :meth:`.authenticate() <CmixAPI.authenticate>`

        :returns: :obj:`None <python:None>` on success

        :raises CmixError: If the API instance has not been authenticated.
        """
        if self._authentication_headers is None:
            raise CmixError('The API instance must be authenticated before calling this method.')

    def authenticate(self, *args, **kwargs):
        """Authenticate the API instance against the Dynata Survey Authoring API.

        :returns: :obj:`None <python:None>` on success

        :raises CmixError: If authentication fails for any reason.
        """

        auth_payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }

        auth_url = '{}/access-token'.format(CMIX_SERVICES['auth'][self.url_type])
        try:
            auth_response = requests.post(
                auth_url,
                json=auth_payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            if auth_response.status_code != 200:
                raise CmixError(
                    'CMIX returned a non-200 response code: {} and error {}'.format(
                        auth_response.status_code,
                        auth_response.text
                    )
                )
        except Exception as e:
            raise CmixError('Could not request authorization from CMIX. Error: {}'.format(e))
        auth_json = auth_response.json()

        self._authentication_headers = {
            'Authorization': '{} {}'.format(auth_json['token_type'], auth_json['access_token'])
        }

    def fetch_banner_filter(self, survey_id, question_a, question_b, response_id):
        """Returns a :term:`Banner Filter` for a given :term:`survey`.

        :returns: A :class:`dict <python:dict>` of the JSON representaton of the
          :term:`banner filter`.
        """
        self.check_auth_headers()
        log.debug(
            'Requesting banner filter for CMIX survey {}, question A: {}, question B: {}, response ID: {}'.format(
                survey_id,
                question_a,
                question_b,
                response_id
            )
        )
        base_url = CMIX_SERVICES['reporting'][self.url_type]
        url = '{}/surveys/{}/response-counts'.format(base_url, survey_id)
        payload = {
            'testYN': 'LIVE',
            'status': 'COMPLETE',
            'counts': [{
                'questionId': question_a,
                'resolution': 1
            }],
            'filters': [{
                'questionId': question_b,
                'responseId': response_id
            }]
        }
        response = requests.post(url, headers=self._authentication_headers, json=payload, timeout=self.timeout)

        return response.json()

    def fetch_raw_results(self, survey_id, payload):
        """Retrieve the identifiers of the questions contained in a given survey.

        :param survey_id: The unique identifier of the survey whose raw results
          should be retrieved.

        :param payload: A collection of :class:`dict <python:dict>` objects where each
          object provides the identifier of a question within the survey that
          should be returned.

          For example:

          .. code-block:: python

            [
              { 'questionId': 122931 },
              { 'questionId': 123456 },
              ...
            ]

        :type payload: :class:`list <python:list>` of :class:`dict <python:dict>`

        :returns: A :class:`dict <python:dict>` of the JSON representaton of the
          respondent values for the survey questions indicated in the
          ``payload``.

        """
        self.check_auth_headers()

        log.debug('Requesting raw results for CMIX survey {}'.format(survey_id))
        base_url = CMIX_SERVICES['reporting'][self.url_type]
        url = '{}/surveys/{}/response-counts'.format(base_url, survey_id)
        response = requests.post(url, headers=self._authentication_headers, json=payload, timeout=self.timeout)

        return response.json()

    def api_get(self,
                endpoint,
                error = ''):
        """Execute a GET request against the Dynata Survey Authoring API.

        :param endpoint: The API endpoint that should be retrieved.
        :type endpoint: :class:`str <python:str>`

        :param error: The heading of the error to return in the error message if
          the API request fails. Defaults to
          `CMIX returned a non-200 response code`.
        :type error: :class:`str <python:str>`

        :returns: A Python representation of the JSON object returned by the API.
        :rtype: :class:`dict <python:dict>` or :class:`list <python:list>`

        :raises CmixError: if the API returned a response with an HTTP Status
          other than 200.

        """
        self.check_auth_headers()
        url = '{}/{}'.format(CMIX_SERVICES['survey'][self.url_type], endpoint)
        response = requests.get(url, headers=self._authentication_headers, timeout=self.timeout)
        if response.status_code != 200:
            if '' == error:
                error = 'CMIX returned a non-200 response code'
            raise CmixError(
                '{}: {} and error {}'.format(
                    error,
                    response.status_code,
                    response.text
                )
            )
        return response.json()

    def api_delete(self, endpoint, error=''):
        """Execute a DELETE request against the Dynata Survey Authoring API.

        :param endpoint: The API endpoint that should be called with a DELETE
          request.
        :type endpoint: :class:`str <python:str>`

        :param error: The heading of the error to return in the error message if
          the API request fails. Defaults to
          `CMIX returned a non-200 response code`.
        :type error: :class:`str <python:str>`

        :returns: A Python representation of the JSON object returned by the API.
        :rtype: :class:`dict <python:dict>` or :class:`list <python:list>`

        :raises CmixError: if the API returned a response with an HTTP Status
          other than 200.

        """
        self.check_auth_headers()
        url = '{}/{}'.format(CMIX_SERVICES['survey'][self.url_type], endpoint)
        response = requests.delete(url, headers=self._authentication_headers, timeout=self.timeout)
        if response.status_code != 200:
            if '' == error:
                error = 'CMIX returned a non-200 response code'
            raise CmixError(
                '{}: {} and error {}'.format(
                    error,
                    response.status_code,
                    response.text
                )
            )
        return response.json()

    def get_surveys(self, status, *args, **kwargs):
        """Retrieve surveys from the Dynata Survey Authoring platform.

        :param status: The status of surveys to retrieve. Accepts either:
          * ``closed`` for surveys that have finished data collection,
          * ``live`` for surveys that have been launched and are collecting data,
          * ``design`` for surveys that have not yet been launched
        :type status: :class:`str <python:str>`

        :param extra_params: Optional collection of URL parameters that should
          be added to the API endpoint URL after the ``status`` parameter.
          Expects each parameter to be supplied as a string like ``KEY=VALUE``.

          Example:

          .. code-block:: python

            extra_params = ['paramKey1=paramValue1', 'paramKey2=paramValue2']

        :type extra_params: :class:`list <python:list>` of :class:`str <python:str>`

        :returns: A collection of :term:`surveys <survey>` that meet the
          criteria supplied to the method, where each survey is represented as a
          :class:`dict <python:dict>` with the following keys:

          * ``id``: The unique ID of the survey
          * ``name``: The human-readable name given to the survey
          * ``token``: A token for the survey
          * ``mxrId``: An internal ID used by the Dynata Survey Authoring tool
          * ``cxNumber``: TBD
          * ``libraryYn``: TBD
          * ``clientId``: TBD
          * ``primaryProgrammerId``: The ID of the user assigned as the primary
            author of the survey.
          * ``secondaryProgrammerId``: The ID of the user assigned as the
            secondary author of the survey.
          * ``status``: The status of the survey.

          .. todo::

            Confirm the documentation of the keys marked as "TBD"

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        """
        self.check_auth_headers()
        base_url = CMIX_SERVICES['survey'][self.url_type]
        surveys_url = '{}/surveys?status={}'.format(base_url, status)
        extra_params = kwargs.get('extra_params')
        if extra_params is not None:
            surveys_url = self.add_extra_url_params(surveys_url, extra_params)

        surveys_response = requests.get(surveys_url, headers=self._authentication_headers, timeout=self.timeout)

        return surveys_response.json()

    def add_extra_url_params(self, url, params):
        """Appends additional URL parameters to the ``url`` supplied.

        :param url: The URL to which parameters should be appended.
        :type url: :class:`str <python:str>`

        :param params: Collection of URL parameters that should
          be appended to ``url``. Expects each parameter to be supplied as a
          string like ``KEY=VALUE``.

          Example:

          .. code-block:: python

            params = ['paramKey1=paramValue1', 'paramKey2=paramValue2']

        :type params: iterable of :class:`str <python:str>`

        :rtype: :class:`str <python:str>`

        """
        for param in params:
            url = '{}&{}'.format(url, param)

        return url

    def get_survey_data_layouts(self, survey_id):
        """Retrieve the :term:`Data Layouts <Data Layout>` for a given survey.

        :param survey_id: The unique ID of the survey whose data layouts should
          be retrieved.

        :returns: Collection of data layout objects in :class:`dict <python:dict>`
          form with the following keys:

          * ``id``: The identifier of the :term:`Data Layout`
          * ``surveyId``: The unique identifier of the survey.
          * ``userId``: TBD
          * ``name``: TBD
          * ``deletedYn``: TBD

          .. todo::

            Confirm the documentation of the keys marked as "TBD"

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status code other than
          ``200``

        """
        self.check_auth_headers()
        data_layouts_url = '{}/surveys/{}/data-layouts'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        data_layouts_response = requests.get(data_layouts_url, headers=self._authentication_headers, timeout=self.timeout)
        if data_layouts_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting data_layouts: {} and error {}'.format(
                    data_layouts_response.status_code,
                    data_layouts_response.text
                )
            )
        return data_layouts_response.json()

    def get_survey_definition(self, survey_id):
        """Retrieve the :term:`Survey Definition` for the survey indicated.

        :param survey_id: The unique ID of the survey whose definition should be
          retrieved.

        :returns: TBD

          .. todo::

            Determine what this method returns.

        """
        self.check_auth_headers()
        definition_url = '{}/surveys/{}/definition'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        definition_response = requests.get(definition_url, headers=self._authentication_headers, timeout=self.timeout)
        return definition_response.json()

    def get_survey_xml(self, survey_id):
        """Retrieve the XML representation of the :term:`Survey Definition` for
        the indicated survey.

        :param survey_id: The unique ID of the survey whose definition should be
          retrieved.

        :returns: The XML representation of the :term:`Survey Definition`.
        :rtype: :class:`str <python:str>` containing XML
        """
        self.check_auth_headers()
        xml_url = '{}/surveys/{}'.format(CMIX_SERVICES['file'][self.url_type], survey_id)
        xml_response = requests.get(xml_url, headers=self._authentication_headers, timeout=self.timeout)
        return xml_response.content

    def get_survey_test_url(self, survey_id):
        """Retrieve the :term:`Test Link` which would allow you to test the
        indicated survey.

        :param survey_id: The unique ID of the survey whose :term:`Test Link`
          should be retrieved.

        :returns: The URL which can be used to test the survey indicated by
          ``survey_id``.
        :rtype: :class:`str <python:str>`

        :raises CmixError: if no :term:`Test Token` is returned
        """
        self.check_auth_headers()
        survey_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        survey_response = requests.get(survey_url, headers=self._authentication_headers, timeout=self.timeout)
        test_token = survey_response.json().get('testToken', None)
        if test_token is None:
            raise CmixError('Survey endpoint for CMIX ID {} did not return a test token.'.format(survey_id))

        test_link = '{}/#/?cmixSvy={}&cmixTest={}'.format(
            CMIX_SERVICES['test'][self.url_type],
            survey_id,
            test_token
        )
        return test_link

    def get_survey_respondents(self, survey_id, respondent_type, live = False):
        """Retrieve metadata about survey :term:`respondents <Respondent>` for
        the indicated survey.

        :param survey_id: The unique ID of the survey whose
          :term:`respondent <Respondent>` meta-data should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :param respondent_type: TBD

          .. todo::

            Determine what this parameter represents.

        :type respondent_type: :class:`str <python:str>`

        :param live: If ``True`` returns :term:`respondent <Respondent>` meta-data
          from respondents who filled out the "live" (launched) survey. Otherwise,
          returns meta-data for respondents who filled out the "test" (pre-launch)
          survey. Defaults to ``False``.
        :type live: :class:`bool <python:bool>`

        :returns: Collection of meta-data describing :term:`respondents <Respondent>`
          who meet the filtering criteria supplied to the method. Each object in
          the collection is a :class:`dict <python:dict>` with the following keys:

          * ``id``: The unique ID of the :term:`Respondent`
          * ``status``: The status of the :term:`Respondent`
          * ``terminationCodeId``: The unique ID of the :term:`Termination Code`
            with which the :term:`Respondent` ended the survey
          * ``startDate``: The timestamp for when the :term:`Respondent` began
            the survey
          * ``endDate``: The timestamp for when the :term:`Respondent` finished
            the survey
          * ``test``: Boolean flag indicating whether the respondent data is
            test or simulated data
          * ``fingerprint``: TBD
          * ``localeId``: The unique ID of the :term:`locale <Locale>` within
            which the :term:`Respondent` took the survey
          * ``pageId``: TBD
          * ``quotaCellId``: TBD
          * ``quotaRowId``: TBD
          * ``quotaId``: TBD
          * ``surveyId``: TBD
          * ``surveySampleSourceId``: TBD
          * ``token``: TBD

          .. todo::

            Determine the meaning of each key marked TBD

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        """
        self.check_auth_headers()
        respondents_url = '{}/surveys/{}/respondents?respondentType={}&respondentStatus={}'.format(
            CMIX_SERVICES['reporting'][self.url_type],
            survey_id,
            "LIVE" if live else "TEST",
            respondent_type,
        )
        respondents_response = requests.get(respondents_url, headers=self._authentication_headers, timeout=self.timeout)
        return respondents_response.json()

    def get_survey_locales(self, survey_id):
        """Retrieve the :term:`locales <Locale>` defined for the indicated survey.

        :param survey_id: The unique ID of the survey whose
          :term:`locales <Locale>` should be retrieved.

        :returns: Collection of :term:`Locale` objects as
          :class:`dict <python:dict>` where each object contains the following
          keys:

          * ``id``: The unique ID of the :term:`Locale`
          * ``surveyId``: The unique ID of the survey
          * ``isoCode``: The ISO code of the :term:`Locale`
          * ``name``: The human-readable name of the :term:`Locale`
          * ``default``: If ``True``, indicates that this is the default
            :term:`Locale` to apply to the survey
          * ``active``: If ``True``, indicates that the :term:`Locale` is active
            or supported by the survey
        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        self.check_auth_headers()
        locales_url = '{}/surveys/{}/locales'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        locales_response = requests.get(locales_url, headers=self._authentication_headers, timeout=self.timeout)
        if locales_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting locales: {} and error {}'.format(
                    locales_response.status_code,
                    locales_response.text
                )
            )
        return locales_response.json()

    def get_survey_status(self, survey_id):
        """Retrieve the status of a survey.

        :param survey_id: The unique ID of the survey whose status should be
          retrieved.

        :returns: The status of the survey. Should return either:

          * ``design`` for surveys that have not yet been launched (are not yet
            collecting data)
          * ``live`` for surveys that have been launched and are collecting data
          * ``closed`` for surveys that are no longer collecting data

        :rtype: :class:`str <python:str>`

        :raises CmixError: if no status is available for the survey
        """
        self.check_auth_headers()
        status_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        status_response = requests.get(status_url, headers=self._authentication_headers, timeout=self.timeout)
        status = status_response.json().get('status', None)
        if status is None:
            raise CmixError('Get Survey Status returned without a status. Response: {}'.format(status_response.json()))

        return status.lower()

    def get_survey_sections(self, survey_id):
        """Retrieve meta-data about the :term:`sections <Survey Section>` of the
        survey indicated.

        :param survey_id: The unique ID of the survey whose
          :term:`section <Survey Section>` meta-data should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :returns: Collection of :term:`Survey Section` objects as
          :class:`dict <python:dict>` with keys:

          * ``id``: The unique ID of the :term:`Survey Section`
          * ``surveyId``: The unique ID of the survey
          * ``name``: The human-readable name of the :term:`Survey Section`
          * ``ordinal``: The ordinal position of the section among all sections
            within the survey
          * ``description``: The description given to the section
          * ``settings``: A dictionary with settings applied to the section
          * ``label``: A human-readable label to apply to the section
          * ``existingSectionId``: TBD

          .. todo::

            Determine the keys marked TBD

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        self.check_auth_headers()
        sections_url = '{}/surveys/{}/sections'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        sections_response = requests.get(sections_url, headers=self._authentication_headers, timeout=self.timeout)
        if sections_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting sections: {} and error {}'.format(
                    sections_response.status_code,
                    sections_response.text
                )
            )
        return sections_response.json()

    def get_survey_sources(self, survey_id):
        """Retrieve the sources for the survey.

        .. todo::

          Confirm that "survey sources" means the sample sources.

        :param survey_id: The unique ID of the survey whose sources should be
          retrieved.
        :type survey_id: :class:`int <python:int>`

        :returns: Collection of :term:`Survey Source` objects as
          :class:`dict <python:dict>` objects with keys:

          * ``id``: The unique ID of the :term:`Survey Source`
          * ``name``: The human-readable name of the :term:`Survey Source`
          * ``token``: TBD

          .. todo::

            Determine the meaning of the keys marked TBD

        """
        self.check_auth_headers()
        sources_url = '{}/surveys/{}/sources'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        sources_response = requests.get(sources_url, headers=self._authentication_headers, timeout=self.timeout)
        if sources_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting sources: {} and error {}'.format(
                    sources_response.status_code,
                    sources_response.text
                )
            )
        return sources_response.json()

    def get_survey_completes(self, survey_id):
        """Retrieve the metadata for COMPLETE respondent records.

        .. note::

          This method is equivalent to calling:

          .. code-block:: python

            .get_survey_respondents(survey_id,
                                    respondetType = 'COMPLETE',
                                    live = True)

        :param survey_id: The unique ID of the survey whose
          :term:`respondent <Respondent>` meta-data should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :returns: Collection of meta-data describing :term:`respondents <Respondent>`
          completed the survey following its launch. Each object in the
          collection is a :class:`dict <python:dict>` with the following keys:

          * ``id``: The unique ID of the :term:`Respondent`
          * ``status``: The status of the :term:`Respondent`
          * ``terminationCodeId``: The unique ID of the :term:`Termination Code`
            with which the :term:`Respondent` ended the survey
          * ``startDate``: The timestamp for when the :term:`Respondent` began
            the survey
          * ``endDate``: The timestamp for when the :term:`Respondent` finished
            the survey
          * ``test``: Boolean flag indicating whether the respondent data is
            test or simulated data
          * ``fingerprint``: TBD
          * ``localeId``: The unique ID of the :term:`locale <Locale>` within
            which the :term:`Respondent` took the survey
          * ``pageId``: TBD
          * ``quotaCellId``: TBD
          * ``quotaRowId``: TBD
          * ``quotaId``: TBD
          * ``surveyId``: TBD
          * ``surveySampleSourceId``: TBD
          * ``token``: TBD

          .. todo::

            Determine the meaning of each key marked TBD

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        .. seealso::

          * :meth:`.get_survey_respondents() <CmixAPI.get_survey_respondents>`

        """

        return self.get_survey_respondents(survey_id, "COMPLETE", True)

    def get_survey_termination_codes(self, survey_id):
        """Retrieve the :term:`Termination Codes <Termination Code>` defined for
        the indicated survey.

        :param survey_id: The unique ID of the survey whose
          :term:`Termination Codes <Termination Code>` should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :returns: Collection of :term:`Termination Code` objects represented as
          :class:`dict <python:dict>` objects with keys:

          * ``id``: Unique ID of the :term:`Termination Code`
          * ``surveyId``: Unique ID of the survey
          * ``name``: Name assigned to the :term:`Termination Code`
          * ``type``: TBD
          * ``questionId``: The unique ID of the question with which the
            :term:`Termination Code` is associated

          .. todo::

            Determine the keys marked TBD

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        self.check_auth_headers()
        termination_codes_url = '{}/surveys/{}/termination-codes'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        termination_codes_response = requests.get(
            termination_codes_url,
            headers=self._authentication_headers,
            timeout=self.timeout
        )
        if termination_codes_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting termination_codes: {} and error {}'.format(
                    termination_codes_response.status_code,
                    termination_codes_response.text
                )
            )
        return termination_codes_response.json()

    def create_export_archive(self, survey_id, export_type):
        """Generate a data file of respondent records from the indicated
        survey.

        :param survey_id: The unique ID of the survey whose respondent data
          should be converted into a downloadable data file.
        :type survey_id: :class:`int <python:int>`

        :param export_type: The type of data file that should be produced.
          Accepts: ``SPSS`` or ``csv``

          .. todo::

            Confirm meaning and acceptable values for ``export_type``

        :type export_type: :class:`str <python:str>`

        :returns: Meta-data about the data file produced, returned as a
          :class:`dict <python:dict>` with the following keys:

          * ``id``: Unique ID of the data file
          * ``dataLayoutId``: unique ID of the :term:`Data Layout` applied to
            the data file
          * ``surveyId``: the unique ID of the survey
          * ``progress``: TBD
          * ``filterStartDate``: the timestamp on or after which respondent records
            who started taking the survey would be included in the data file
          * ``filterEndDate``: the timestamp on or before which respondent records
            who finished taking the survey would be included in the data file
          * ``respondentType``: the type of respondent records contained in the
            data file
          * ``fileName``: the filename of the data file
          * ``type``: the file type of the data file
          * ``status``: the status of the data file
          * ``archiveUrl``: the URL from which the data file may be retrieved
          * ``deletedYn``: TBD
          * ``completes``: if ``True``, indicates that the data file contains
            COMPLETE records (i.e. records where the respondent finished the
            survey)
          * ``inProcess``: if ``True``, indicates that the data file contains
            PARTIAL records (i.e. records where the respondent has begun but not
            yet finished the survey)
          * ``terminates``: if ``True``, indicates that the data file contains
            TERMINATED records (i.e. records where the respondent was exited
            from the survey based on the survey logic)

        :rtype: :class:`dict <python:dict>`

        :raises CmixError: if the API returned an HTTP Status Code other than
          ``200`` when generating the data file

        :raises CmixError: if an error occurred when generating the data file

        :raises CmixError: if the survey did not have a default
          :term:`Data Layout`

        """
        self.check_auth_headers()
        archive_url = '{}/surveys/{}/archives'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        headers = self._authentication_headers.copy()
        headers['Content-Type'] = "application/json"
        payload = {
            "respondentType": "LIVE",
            "type": export_type,
            "completes": True,
            "inProcess": False,
            "terminates": False
        }

        archive_response = requests.post(archive_url, json=payload, headers=headers, timeout=self.timeout)
        if archive_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code: {} and error {}'.format(
                    archive_response.status_code,
                    archive_response.text
                )
            )
        if archive_response.json().get('error', None) is not None:
            raise CmixError(
                'CMIX returned an error with status code {}: {}'.format(
                    archive_response.status_code,
                    archive_response.text
                )
            )
        archive_json = archive_response.json()

        layout_json = self.get_survey_data_layouts(survey_id)
        layout_id = None
        for layout in layout_json:
            if layout.get('name') == 'Default':
                layout_id = layout.get('id')
        if layout_id is None:
            raise CmixError(
                'Layouts response did not contain a "Default" layout.'
            )

        archive_json['dataLayoutId'] = layout_id

        return archive_json

    def get_archive_status(self, survey_id, archive_id, layout_id):
        """Retrieve the meta-data for a data file export (data archive).

        :param survey_id: The unique ID of the survey whose archive meta-data
          should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :param archive_id: The unique ID of the data file whose meta-data should
          be retrieved.
        :type archive_id: :class:`int <python:int>`

        :param layout_id: The unique ID of the data layout applied to the data
          file whose meta-data should be retrieved.
        :type layout_id: :class:`int <python:int>`

        :returns: Meta-data about the data file produced, returned as a
          :class:`dict <python:dict>` with the following keys:

          * ``id``: Unique ID of the data file
          * ``dataLayoutId``: unique ID of the :term:`Data Layout` applied to
            the data file
          * ``surveyId``: the unique ID of the survey
          * ``progress``: TBD
          * ``filterStartDate``: the timestamp on or after which respondent records
            who started taking the survey would be included in the data file
          * ``filterEndDate``: the timestamp on or before which respondent records
            who finished taking the survey would be included in the data file
          * ``respondentType``: the type of respondent records contained in the
            data file
          * ``fileName``: the filename of the data file
          * ``type``: the file type of the data file
          * ``status``: the status of the data file
          * ``archiveUrl``: the URL from which the data file may be retrieved
          * ``deletedYn``: TBD
          * ``completes``: if ``True``, indicates that the data file contains
            COMPLETE records (i.e. records where the respondent finished the
            survey)
          * ``inProcess``: if ``True``, indicates that the data file contains
            PARTIAL records (i.e. records where the respondent has begun but not
            yet finished the survey)
          * ``terminates``: if ``True``, indicates that the data file contains
            TERMINATED records (i.e. records where the respondent was exited
            from the survey based on the survey logic)

        :rtype: :class:`dict <python:dict>`

        :raises CmixError: if ``layout_id`` is :obj:`None <python:None>`

        :raises CmixError: if ``archive_id`` is :obj:`None <python:None>`

        :raises CmixError: if the API returned an HTTP Status Code other than ``200``

        """
        self.check_auth_headers()
        if layout_id is None:
            raise CmixError('Error while updating archive status: layout ID is None. Archive ID: {}'.format(archive_id))
        if archive_id is None:
            raise CmixError(
                'Error while updating archive status: CMIX archive ID is None. Archive ID: {}'.format(archive_id)
            )
        base_url = CMIX_SERVICES['survey'][self.url_type]
        archive_url = '{}/surveys/{}/data-layouts/{}/archives/{}'.format(
            base_url,
            survey_id,
            layout_id,
            archive_id  # The archive ID on CMIX.
        )
        archive_response = requests.get(archive_url, headers=self._authentication_headers, timeout=self.timeout)
        if archive_response.status_code > 299:
            raise CmixError(
                'CMIX returned an invalid response code getting archive status: HTTP {} and error {}'.format(
                    archive_response.status_code,
                    archive_response.text
                )
            )

        return archive_response.json()

    def update_project(self, project_id, status = None):
        """Update the status of a survey project.

        :param project_id: The unique ID of the :term:`Project` whose status
          should be updated.
        :type project_id: :class:`int <python:int>`

        :param status: The status that should be applied to the :term:`Project`.
          Defaults to :obj:`None <python:None>`. Accepts:

            * ``LIVE`` to launch the survey (start data collection)
            * ``CLOSED`` to close/finish the survey (end data collection)
            * ``DESIGN`` to switch the survey to design-mode

            .. todo::

              Confirm acceptable values.

        :type status: :class:`str <python:str>`

        :returns: The :class:`Response <requests:Response>` object for the API
          request
        :rtype: :class:`requests.Response <requests:Response>`

        :raises CmixError: if ``status`` was empty

        :raises CmixError: if the API returns an HTTP Status code greater than `299`

        """
        self.check_auth_headers()

        payload_json = {}
        if status is not None:
            payload_json['status'] = status

        if payload_json == {}:
            raise CmixError("No update data was provided for CMIX Project {}".format(project_id))

        url = '{}/projects/{}'.format(CMIX_SERVICES['survey'][self.url_type], project_id)
        response = requests.patch(url, json=payload_json, headers=self._authentication_headers, timeout=self.timeout)

        if response.status_code > 299:
            raise CmixError(
                'CMIX returned an invalid response code during project update: HTTP {} and error {}'.format(
                    response.status_code,
                    response.text
                )
            )
        return response

    def create_survey(self, xml_string):
        """Create a survey and set its status to ``LIVE``.

        .. todo::

          Verify whether this is actually what this funciton does. Looking at
          the Python source code, it seems that it sets the survey's status to
          ``DESIGN``

        :param xml_string: A complete definition of the survey in XML format.

          .. todo::

            Document the XML structure of the survey.

        :type xml_string: :class:`str <python:str>`

        :returns: The :class:`Response <requests:Response>` object for the API
          request
        :rtype: :class:`requests.Response <requests:Response>`

        :raises CmixError: if the API returns an HTTP Status Code greater than ``299``

        """
        self.check_auth_headers()

        url = '{}/surveys/data'.format(CMIX_SERVICES['file'][self.url_type])
        payload = {"data": xml_string}
        response = requests.post(url, payload, headers=self._authentication_headers, timeout=self.timeout)

        if response.status_code > 299:
            raise CmixError(
                'Error while creating survey. CMIX responded with status' +
                ' code {} and text: {} when sent this XML: {}'.format(
                    response.status_code,
                    response.text,
                    xml_string
                )
            )
        response_json = response.json()

        self.update_project(response_json.get('projectId'),
                            status = self.SURVEY_STATUS_DESIGN)

        return response_json

    def get_survey_simulations(self, survey_id):
        """Retrieve :term:`Survey Simulations <Survey Simulation>` meta-data for
        the indicated survey.

        :param survey_id: The unique ID of the survey whose simulation meta-data
          should be retrieved.
        :type survey_id: :class:`int <python:int>`

        :returns: Collection of :term:`Survey Simulation` objects represented as
          :class:`dict <python:dict>` with keys:

          * ``id``: the unique ID of the :term:`Survey Simulation`
          * ``userId``: the unique ID of the user who generated the simulated
            data
          * ``surveyId``: the unique ID of the survey
          * ``name``: the name given to the simulated dataset
          * ``respondentCount``: the number of respondents that were simulated
          * ``completesCount``: the number of COMPLETED records that were simulated
          * ``terminatesCount``: the number of TERMINATED records that were simualted
          * ``dropOutCount``: the number of DROP-OUT (not finished) records that
            were simulated
          * ``requestedCount``: the number of records that were requested
          * ``requestedCompletesCount``: the number of COMPLETED records that
            were requested
          * ``dateCreated``: the timestamp for when the simulation was created
          * ``dateModified``: the timestamp for when the simulation was last modified
          * ``template``: TBD
          * ``user``: an embedded object describing the user who generated the
            simulated dataset

          .. todo::

            Verify what this function actually returns.

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        self.check_auth_headers()
        simulations_url = '{}/surveys/{}/simulations'.format(CMIX_SERVICES['survey'][self.url_type], survey_id)
        simulations_response = requests.get(simulations_url, headers=self._authentication_headers, timeout=self.timeout)

        if simulations_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code while getting simulations: {} and error {}'.format(
                    simulations_response.status_code,
                    simulations_response.text
                )
            )

        return simulations_response.json()

    def get_projects(self):
        """Retrieve a collection of :term:`Projects <Project>` from the
        Dynata Survey Authoring system.

        :returns: A collection of :term:`Project` objects with meta-data
          represented as :class:`dict <python:dict>` with keys:

          .. todo::

            Determine the keys that are returned.

        :rtype: :class:`list <python:list>` of :class:`dict <python:dict>`

        """
        project_endpoint = 'projects'
        project_error = 'CMIX returned a non-200 response code while getting projects'
        project_response = self.api_get(project_endpoint, project_error)

        return project_response
