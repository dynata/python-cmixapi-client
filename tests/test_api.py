# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import mock

from unittest import TestCase
from CmixAPIClient.api import CmixAPI, CMIX_SERVICES
from CmixAPIClient.error import CmixError


def default_cmix_api():
    return CmixAPI(
        username="test_username",
        password="test_password",
        client_id="test_client_id",
        client_secret="test_client_secret"
    )


class TestCmixAPI(TestCase):
    def setUp(self):
        self.cmix_api = default_cmix_api()
        self.cmix_api._authentication_headers = {'Authorization': 'Bearer test'}
        self.survey_id = 1337

    def test_cmix_authentication_check(self):
        with self.assertRaises(CmixError):
            CmixAPI()

    def test_cmix_authenticate(self):
        with mock.patch('requests.post') as mock_request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'token_type': 'Bearer',
                'access_token': 'tokentokentoken',
            }
            mock_request.return_value = mock_response
            self.cmix_api.authenticate()
        correct_auth_header = {'Authorization': 'Bearer tokentokentoken'}
        self.assertEqual(self.cmix_api._authentication_headers, correct_auth_header)

    def test_cmix_authenticate_error_handled(self):
        with mock.patch('requests.post') as mock_request:
            mock_response = mock.Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                'token_type': 'Bearer',
                'access_token': 'tokentokentoken',
            }
            mock_request.return_value = mock_response
            with self.assertRaises(CmixError):
                self.cmix_api.authenticate()

    def test_create_export_archive(self):
        with mock.patch('requests.post') as mock_post:
            mock_post_response = mock.Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                'response': 1,
            }
            mock_post.return_value = mock_post_response
            with mock.patch('requests.get') as mock_get:
                mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Default'
                }]
                mock_get.return_value = mock_response
                response = self.cmix_api.create_export_archive(self.survey_id, 'XLSX_READABLE')
        self.assertEqual(response['response'], 1)

    def test_create_export_archive_errors_handled(self):
        with mock.patch('CmixAPIClient.api.requests.post') as mock_post:
            mock_post_response = mock.Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                'response': 1,
                'error': 'Oops!',
            }
            mock_post.return_value = mock_post_response
            with mock.patch('CmixAPIClient.api.requests.get') as mock_get:
                # Check CmixError is raised if POST response JSON includes an error.
                mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Default',
                }]
                mock_get.return_value = mock_response
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.survey_id, 'XLSX_READABLE')

            # Remove error from POST response.
            mock_post_response.json.return_value = {'response': 1}

            with mock.patch('CmixAPIClient.api.requests.get') as mock_get:
                # Check CmixError is raised on GET 500 response. (layout response)
                mock_response = mock.Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Default',
                }]
                mock_get.return_value = mock_response
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.survey_id, 'XLSX_READABLE')

                # Check CmixError is raised if no default layout is returned.
                mock_response.status_code = 200
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Not Default',
                }]
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.survey_id, 'XLSX_READABLE')

    def test_get_survey_data_layouts(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}

        # success case
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            self.cmix_api.get_survey_data_layouts(self.survey_id)

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            surveys_url = '{}/surveys/{}/data-layouts'.format(base_url, self.survey_id)
            mock_request.get.assert_any_call(surveys_url, headers=self.cmix_api._authentication_headers)

        # error case (survey not found)
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 404
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                self.cmix_api.get_survey_data_layouts(self.survey_id)

    def test_get_survey_status(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}

        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {'status': 'LIVE'}
            mock_request.get.return_value = mock_get

            self.assertEqual(self.cmix_api.get_survey_status(self.survey_id), 'live')

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            surveys_url = '{}/surveys/{}'.format(base_url, self.survey_id)
            mock_request.get.assert_any_call(surveys_url, headers=self.cmix_api._authentication_headers)

    def test_get_survey_status_error_handled(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}

        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                self.cmix_api.get_survey_status(self.survey_id)

    def test_get_survey_test_url(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}
        correct_test_link = '{}/#/?cmixSvy={}&cmixTest={}'.format(
            CMIX_SERVICES['test']['BASE_URL'], self.survey_id, 'test')

        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {'testToken': 'test'}
            mock_request.get.return_value = mock_get

            self.assertEqual(self.cmix_api.get_survey_test_url(self.survey_id), correct_test_link)

    def test_get_survey_test_url_no_token_handled(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                self.cmix_api.get_survey_test_url(self.survey_id)

    def test_get_survey_completes(self):
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_post = mock.Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                'response': '1',
                'token_type': 'test',
                'access_token': 'test',
            }
            mock_request.post.return_value = mock_post
            mock_respondents = dict((k, v) for k, v in enumerate(range(10)))
            mock_request.get.side_effect = [
                mock.Mock(json=lambda: mock_respondents),
            ]
            self.assertEqual(self.cmix_api.get_survey_completes(self.survey_id), mock_respondents)

    def test_get_surveys(self):
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_post = mock.Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                'response': '1',
                'token_type': 'test',
                'access_token': 'test',
            }
            mock_request.post.return_value = mock_post
            mock_surveys = dict((k, v) for k, v in enumerate(range(10)))
            mock_request.get.side_effect = [
                mock.Mock(json=lambda: mock_surveys),
                mock.Mock(json=lambda: mock_surveys),
            ]
            self.cmix_api.get_surveys('LIVE')
            expected_url = '{}/surveys?status={}'.format(CMIX_SERVICES['survey']['BASE_URL'], 'LIVE')
            mock_request.get.assert_any_call(expected_url, headers=mock.ANY)

            expected_url_with_params = '{}/surveys?status={}&hello=world&test=params'.format(
                CMIX_SERVICES['survey']['BASE_URL'], 'LIVE')
            self.cmix_api.get_surveys('LIVE', extra_params=["hello=world", "test=params"])
            mock_request.get.assert_any_call(expected_url_with_params, headers=self.cmix_api._authentication_headers)

    def test_fetch_banner_filter(self):
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_post = mock.Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                'response': '1',
                'token_type': 'test',
                'access_token': 'test',
            }
            mock_request.post.return_value = mock_post
            mock_respondents = dict((k, v) for k, v in enumerate(range(10)))
            mock_request.get.side_effect = [
                mock.Mock(json=lambda: mock_respondents),
            ]
            question_a = 123
            question_b = 124
            response_id = 125
            self.cmix_api.fetch_banner_filter(self.survey_id, question_a, question_b, response_id)
            expected_url = '{}/surveys/{}/response-counts'.format(
                CMIX_SERVICES['reporting']['BASE_URL'], self.survey_id)
            expected_payload = {
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
            mock_request.post.assert_any_call(expected_url, json=expected_payload, headers=mock.ANY)

    def test_get_archive_status(self):
        survey_id = 1337
        archive_id = 12
        layout_id = 1
        with mock.patch('CmixAPIClient.api.requests.get') as mock_request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'COMPLETE',
                'archiveUrl': 'http://popresearch.com/',
            }

            mock_request.return_value = mock_response
            response = self.cmix_api.get_archive_status(survey_id, archive_id, layout_id)
        self.assertEqual(response['status'], 'COMPLETE')
        self.assertEqual(response['archiveUrl'], 'http://popresearch.com/')

    def test_error_if_not_authenticated(self):
        self.cmix_api._authentication_headers = None
        with self.assertRaises(CmixError):
            self.cmix_api.get_surveys(CmixAPI.SURVEY_STATUS_LIVE)

    def test_add_extra_url_params(self):
        url = 'url.com?status=CLOSED'
        extra_params = ['key1=value1', 'key2=value2']
        result = self.cmix_api.add_extra_url_params(url, extra_params)
        extra_params_formatted = '&{}&{}'.format(extra_params[0], extra_params[1])
        expected = '{}{}'.format(url, extra_params_formatted)
        self.assertEqual(result, expected)
