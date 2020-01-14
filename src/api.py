# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import logging

from .error import CmixError

log = logging.getLogger(__name__)

CMIX_SERVICES = {
    'auth': {
        'BASE_URL': 'https://auth.cmix.com',
    },
    'file': {
        'BASE_URL': 'https://file-processing.cmix.com',
    },
    'launchpad': {
        'BASE_URL': 'https://launchpad.cmix.com',
    },
    'reporting': {
        'BASE_URL': 'https://reporting-api.cmix.com',
    },
    'survey': {
        'BASE_URL': 'https://survey-api.cmix.com',
    },
    'test': {
        'BASE_URL': 'https://test.cmix.com',
    },
}


# - it seems like this class would work better as a singleton - and
#   maybe the method above (default_cmix_api) could create the singleton,
#   authenticate it, then return it - and all subsequent calls to
#   default_cmix_api would return the same authenticated singleton - no need
#   to keep authenticating on every request
# - default_cmix_api could also check_auth_headers before returning the
#   singleton - if it's not authenticated it could try authenticating or
#   creating a new instance THEN authenticating
class CmixAPI(object):
    # valid survey statuses
    SURVEY_STATUS_DESIGN = 'DESIGN'
    SURVEY_STATUS_LIVE = 'LIVE'
    SURVEY_STATUS_CLOSED = 'CLOSED'

    # valid extra survey url params
    SURVEY_PARAMS_STATUS_AFTER = 'statusAfter'

    def __init__(self, username=None, password=None, client_id=None, client_secret=None, *args, **kwargs):
        if None in [username, password, client_id, client_secret]:
            raise CmixError("All authentication data is required.")
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret

    def check_auth_headers(self):
        if self._authentication_headers is None:
            raise CmixError('The API instance must be authenticated before calling this method.')

    def authenticate(self, *args, **kwargs):
        auth_payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }

        auth_url = '{}/access-token'.format(CMIX_SERVICES['auth']['BASE_URL'])
        try:
            auth_response = requests.post(auth_url, json=auth_payload, headers={"Content-Type": "application/json"})
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
        self.check_auth_headers()
        log.debug(
            'Requesting banner filter for CMIX survey {}, question A: {}, question B: {}, response ID: {}'.format(
                survey_id,
                question_a,
                question_b,
                response_id
            )
        )
        base_url = CMIX_SERVICES['reporting']['BASE_URL']
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
        response = requests.post(url, headers=self._authentication_headers, json=payload)
        return response.json()

    def fetch_raw_results(self, survey_id, payload):
        '''
            This calls the CMIX Reporting API 'response-counts' endpoint and returns
            the data for all of the questions in the survey.

            The payload is a set of JSON objects only containing a question ID.
            eg. [
                {'questionId': 122931},
                {...}
            ]
        '''
        self.check_auth_headers()
        log.debug('Requesting raw results for CMIX survey {}'.format(survey_id))
        base_url = CMIX_SERVICES['reporting']['BASE_URL']
        url = '{}/surveys/{}/response-counts'.format(base_url, survey_id)
        response = requests.post(url, headers=self._authentication_headers, json=payload)
        return response.json()

    def get_surveys(self, status, *args, **kwargs):
        '''kwargs:

        extra_params: array of additional url params added to the end of the
        url after the 'status' param, they should be passed in as formatted
        strings like this:
            params = ['paramKey1=paramValue1', 'paramKey2=paramValue2']
            get_surveys('status', extra_params=params)
        '''
        self.check_auth_headers()
        base_url = CMIX_SERVICES['survey']['BASE_URL']
        surveys_url = '{}/surveys?status={}'.format(base_url, status)
        extra_params = kwargs.get('extra_params')
        if extra_params is not None:
            surveys_url = self.add_extra_url_params(surveys_url, extra_params)
        surveys_response = requests.get(surveys_url, headers=self._authentication_headers)
        return surveys_response.json()

    def add_extra_url_params(self, url, params):
        for param in params:
            url = '{}&{}'.format(url, param)

        return url

    def get_survey_definition(self, survey_id):
        self.check_auth_headers()
        definition_url = '{}/surveys/{}/definition'.format(CMIX_SERVICES['survey']['BASE_URL'], survey_id)
        definition_response = requests.get(definition_url, headers=self._authentication_headers)
        return definition_response.json()

    def get_survey_xml(self, survey_id):
        self.check_auth_headers()
        xml_url = '{}/surveys/{}'.format(CMIX_SERVICES['file']['BASE_URL'], survey_id)
        xml_response = requests.get(xml_url, headers=self._authentication_headers)
        return xml_response.content

    def get_survey_test_url(self, survey_id):
        self.check_auth_headers()
        survey_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], survey_id)
        survey_response = requests.get(survey_url, headers=self._authentication_headers)
        test_token = survey_response.json().get('testToken', None)
        if test_token is None:
            raise CmixError('Survey endpoint for CMIX ID {} did not return a test token.'.format(survey_id))
        test_link = '{}/#/?cmixSvy={}&cmixTest={}'.format(
            CMIX_SERVICES['test']['BASE_URL'],
            survey_id,
            test_token
        )
        return test_link

    def get_survey_respondents(self, survey_id, respondent_type, live):
        self.check_auth_headers()
        respondents_url = '{}/surveys/{}/respondents?respondentType={}&respondentStatus={}'.format(
            CMIX_SERVICES['reporting']['BASE_URL'],
            survey_id,
            "LIVE" if live else "TEST",
            respondent_type,
        )
        respondents_response = requests.get(respondents_url, headers=self._authentication_headers)
        return respondents_response.json()

    def get_survey_status(self, survey_id):
        self.check_auth_headers()
        status_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], survey_id)
        status_response = requests.get(status_url, headers=self._authentication_headers)
        status = status_response.json().get('status', None)
        if status is None:
            raise CmixError('Get Survey Status returned without a status. Response: {}'.format(status_response.json()))
        return status.lower()

    def get_survey_completes(self, survey_id):
        return self.get_survey_respondents(survey_id, "COMPLETE", True)

    def create_export_archive(self, survey_id, export_type):
        self.check_auth_headers()
        archive_url = '{}/surveys/{}/archives'.format(CMIX_SERVICES['survey']['BASE_URL'], survey_id)
        headers = self._authentication_headers.copy()
        headers['Content-Type'] = "application/json"
        payload = {
            "respondentType": "LIVE",
            "type": export_type,
            "completes": True,
            "inProcess": False,
            "terminates": False
        }

        archive_response = requests.post(archive_url, json=payload, headers=headers)
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

        layout_url = '{}/surveys/{}/data-layouts/'.format(CMIX_SERVICES['survey']["BASE_URL"], survey_id)
        layout_response = requests.get(layout_url, headers=self._authentication_headers)
        if layout_response.status_code != 200:
            raise CmixError(
                'CMIX returned a non-200 response code: {} and error {}'.format(
                    layout_response.status_code,
                    layout_response.text
                )
            )
        layout_id = None
        for layout in layout_response.json():
            if layout.get('name') == 'Default':
                layout_id = layout.get('id')
        if layout_id is None:
            raise CmixError(
                'Layouts response did not contain a "Default" layout. Response Code: {}, Body {}'.format(
                    layout_response.status_code,
                    layout_response.content
                )
            )

        archive_json['dataLayoutId'] = layout_id
        return archive_json

    def get_archive_status(self, survey_id, archive_id, layout_id):
        self.check_auth_headers()
        if layout_id is None:
            raise CmixError('Error while updating archie status: layout ID is None. Archive ID: {}'.format(archive_id))
        if archive_id is None:
            raise CmixError(
                'Error while updating archie status: CMIX archive ID is None. Pop Archive ID: {}'.format(archive_id)
            )
        archive_url = '{}/surveys/{}/data-layouts/{}/archives/{}'.format(
            CMIX_SERVICES['survey']["BASE_URL"],
            survey_id,
            layout_id,
            archive_id  # The archive ID on CMIX.
        )
        archive_response = requests.get(archive_url, headers=self._authentication_headers)
        if archive_response.status_code > 299:
            raise CmixError(
                'CMIX returned an invalid response code getting archive status: HTTP {} and error {}'.format(
                    archive_response.status_code,
                    archive_response.text
                )
            )
        return archive_response.json()

    def update_project(self, project_id, status=None):
        '''
            NOTE: This endpoint accepts a project ID, not a survey ID.
        '''
        self.check_auth_headers()

        payload_json = {}
        if status is not None:
            payload_json['status'] = status

        if payload_json == {}:
            raise CmixError("No update data was provided for CMIX Project {}".format(project_id))

        url = '{}/projects/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], project_id)
        response = requests.patch(url, json=payload_json, headers=self._authentication_headers)
        if response.status_code > 299:
            raise CmixError(
                'CMIX returned an invalid response code during project update: HTTP {} and error {}'.format(
                    response.status_code,
                    response.text
                )
            )
        return response

    def create_survey(self, xml_string):
        '''
            This function will create a survey on CMIX and set the survey's status to 'LIVE'.
        '''
        self.check_auth_headers()

        url = '{}/surveys/data'.format(CMIX_SERVICES['file']['BASE_URL'])
        payload = {"data": xml_string}
        response = requests.post(url, payload, headers=self._authentication_headers)
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
        self.update_project(response_json.get('projectId'), status=self.SURVEY_STATUS_DESIGN)
        return response_json
