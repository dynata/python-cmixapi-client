# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import logging
import os

from popresearch.models import CmixDataArchive, CmixSurvey, CmixSurveyXml

from .error import CmixError
from .parsing import generate_survey_xml_strings_and_secondary_keys

log = logging.getLogger(__name__)

CMIX_SERVICES = {
    'auth': {
        'BASE_URL': os.getenv('CMIX_URL_AUTH'),
    },
    'launchpad': {
        'BASE_URL': os.getenv('CMIX_URL_LAUNCHPAD'),
    },
    'reporting': {
        'BASE_URL': os.getenv('CMIX_URL_REPORTING'),
    },
    'survey': {
        'BASE_URL': os.getenv('CMIX_URL_SURVEY'),
    },
    'file': {
        'BASE_URL': os.getenv('CMIX_URL_FILE'),
    },
    'test': {
        'BASE_URL': os.getenv('CMIX_URL_TEST'),
    },
}


def default_cmix_api():
    return CmixAPI(
        username=os.getenv("CMIX_USERNAME"),
        password=os.getenv("CMIX_PASSWORD"),
        client_id=os.getenv("CMIX_V2_CLIENT_ID"),
        client_secret=os.getenv("CMIX_V2_CLIENT_SECRET")
    )


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

    def get_survey_definition(self, cmix_survey_id):
        self.check_auth_headers()
        definition_url = '{}/surveys/{}/definition'.format(CMIX_SERVICES['survey']['BASE_URL'], cmix_survey_id)
        definition_response = requests.get(definition_url, headers=self._authentication_headers)
        return definition_response.json()

    def get_survey_xml(self, cmix_survey_id):
        self.check_auth_headers()
        xml_url = '{}/surveys/{}'.format(CMIX_SERVICES['file']['BASE_URL'], cmix_survey_id)
        xml_response = requests.get(xml_url, headers=self._authentication_headers)
        return xml_response.content

    def get_survey_test_url(self, cmix_survey_id):
        self.check_auth_headers()
        survey_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], cmix_survey_id)
        survey_response = requests.get(survey_url, headers=self._authentication_headers)
        test_token = survey_response.json().get('testToken', None)
        if test_token is None:
            raise CmixError('Survey endpoint for CMIX ID {} did not return a test token.'.format(cmix_survey_id))
        test_link = '{}/#/?cmixSvy={}&cmixTest={}'.format(
            CMIX_SERVICES['test']['BASE_URL'],
            cmix_survey_id,
            test_token
        )
        return test_link

    def get_survey_respondents(self, cmix_survey_id, respondent_type, live):
        self.check_auth_headers()
        respondents_url = '{}/surveys/{}/respondents?respondentType={}&respondentStatus={}'.format(
            CMIX_SERVICES['reporting']['BASE_URL'],
            cmix_survey_id,
            "LIVE" if live else "TEST",
            respondent_type,
        )
        respondents_response = requests.get(respondents_url, headers=self._authentication_headers)
        return respondents_response.json()

    def get_survey_status(self, cmix_survey_id):
        self.check_auth_headers()
        status_url = '{}/surveys/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], cmix_survey_id)
        status_response = requests.get(status_url, headers=self._authentication_headers)
        status = status_response.json().get('status', None)
        if status is None:
            raise CmixError('Get Survey Status returned without a status. Response: {}'.format(status_response.json()))
        return status.lower()

    def get_survey_completes(self, cmix_survey_id):
        return self.get_survey_respondents(cmix_survey_id, "COMPLETE", True)

    def create_export_archive(self, cmix_survey, export_type):
        self.check_auth_headers()
        archive_url = '{}/surveys/{}/archives'.format(CMIX_SERVICES['survey']['BASE_URL'], cmix_survey.cmix_id)
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

        layout_url = '{}/surveys/{}/data-layouts/'.format(CMIX_SERVICES['survey']["BASE_URL"], cmix_survey.cmix_id)
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
        cda = CmixDataArchive.objects.create(
            cmix_survey=cmix_survey,
            status=CmixDataArchive.UNPROCESSED,
            json=archive_json,
            download_url="",
            deleted=False,
            file_type=export_type,
        )
        return cda

    def update_archive_status(self, archive):
        self.check_auth_headers()
        layout_id = archive.json.get('dataLayoutId', None)
        archive_id = archive.json.get('id', None)
        if layout_id is None:
            raise CmixError('Error while updating archie status: layout ID is None. Archive ID: {}'.format(archive.id))
        if archive_id is None:
            raise CmixError(
                'Error while updating archie status: CMIX archive ID is None. Pop Archive ID: {}'.format(archive.id)
            )
        archive_url = '{}/surveys/{}/data-layouts/{}/archives/{}'.format(
            CMIX_SERVICES['survey']["BASE_URL"],
            archive.cmix_survey.cmix_id,
            layout_id,
            archive_id  # The archive ID on CMIX.
        )
        archive_response = requests.get(archive_url, headers=self._authentication_headers).json()
        if archive_response.get('status') != "COMPLETE":
            # Save the updated json, but make sure to preserve the layout and archive IDs in case there's a problem.
            archive_response['dataLayoutId'] = layout_id
            archive_response['id'] = archive_id
            archive.json = archive_response
        else:
            archive.status = CmixDataArchive.PROCESSED
            archive.download_url = archive_response.get('archiveUrl')
        archive.save()
        return archive

    def update_project(self, projectId, status=None):
        '''
            NOTE: This endpoint accepts a project ID, not a survey ID.
        '''
        self.check_auth_headers()

        payload_json = {}
        if status is not None:
            payload_json['status'] = status

        if payload_json == {}:
            raise CmixError("No update data was provided for CMIX Project {}".format(projectId))

        url = '{}/projects/{}'.format(CMIX_SERVICES['survey']['BASE_URL'], projectId)
        response = requests.patch(url, json=payload_json, headers=self._authentication_headers)
        if response.status_code > 299:
            raise CmixError(
                'CMIX returned an invalid response code during project update: HTTP {} and error {}'.format(
                    response.status_code,
                    response.text
                )
            )
        return response

    def create_survey(self, survey, wave_number=None):
        '''
            This function will create a survey on CMIX and set the survey's status to 'LIVE'.
        '''
        self.check_auth_headers()

        log.debug('Sending Survey to new CMIX API: {}'.format(survey.name))
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(survey, wave_number)
        cmix_responses = []
        for secondary_key, xml_string in strings_and_keys:
            # Don't try to create survey if there's alread one there
            if CmixSurvey.objects.filter(survey=survey, secondary_key=secondary_key).exists():
                continue

            # Give up after 10 tries
            if survey.failed_creation_attempts >= 10:
                continue

            url = '{}/surveys/data'.format(CMIX_SERVICES['file']['BASE_URL'])
            payload = {"data": xml_string}
            response = requests.post(url, payload, headers=self._authentication_headers)
            cmix_responses.append(response)
            if response.status_code > 299:
                survey.failed_creation_attempts = survey.failed_creation_attempts + 1
                survey.save()
                raise CmixError(
                    'Error while creating survey. CMIX responded with status' +
                    ' code {} and text: {} when sent this XML: {}'.format(
                        response.status_code,
                        response.text,
                        xml_string
                    )
                )
            response_json = response.json()
            cmix_id = response_json.get('id')
            cmix_project_id = response_json.get('projectId')
            log.debug('Successfully created CMIX Survey {}.'.format(cmix_id))

            CmixSurvey.objects.create(
                survey=survey,
                cmix_id=cmix_id,
                cmix_project_id=cmix_project_id,
                status='created',
                cmix_status='design',
                results_requested=False,
                secondary_key=secondary_key,
            )
            CmixSurveyXml.objects.create(
                cmix_id=cmix_id,
                cmix_project_id=cmix_project_id,
                xml=xml_string,
                when_recorded='sent',
            )

            self.update_project(response_json.get('projectId'), status=self.SURVEY_STATUS_DESIGN)

        return cmix_responses
