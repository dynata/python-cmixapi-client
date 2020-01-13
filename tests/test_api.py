# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import io
import json
import mock
import xml.etree.ElementTree as ElementTree
import xmlformatter

from bs4 import BeautifulSoup
from unittest import TestCase
from freezegun import freeze_time

from src.api import CmixAPI, default_cmix_api, CMIX_SERVICES
from src.error import CmixError

from popresearch.cmix.parsing.concepts import create_legacy_concept
from popresearch.cmix.parsing.logic import create_page_logic
from popresearch.cmix.parsing.page import create_media_page, create_question_page
from popresearch.cmix.parsing.section import create_demographic_questions_section
from popresearch.cmix.parsing.survey import generate_survey_xml, \
    generate_survey_xml_string, generate_survey_xml_strings_and_secondary_keys
from popresearch.models import SURVEY_TYPE_COMPARISON, SURVEY_TYPE_CREATIVE, \
    SURVEY_TYPE_CUSTOM, SURVEY_TYPE_DESIGN, SURVEY_TYPE_INSTANT, \
    SURVEY_TYPE_FORCEDEXPOSURE, SURVEY_TYPE_TRACKING, \
    CmixDataArchive, CmixSurvey, \
    Survey

from .factories import SurveyFactory, UserFactory


class TestCmixAPI(TestCase):
    def setUp(self):
        self.cmix_api = default_cmix_api()
        self.cmix_api._authentication_headers = {'Authorization': 'Bearer test'}
        self.user = UserFactory.create_safe()
        self.survey = Survey.objects.create(user=self.user, name="Test Survey")
        self.cmix_survey = CmixSurvey.objects.create(survey=self.survey, cmix_id=42)

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
                self.cmix_api.create_export_archive(self.cmix_survey, 'XLSX_READABLE')
        self.assertEqual(CmixDataArchive.objects.all().count(), 1)

    def test_create_export_archive_errors_handled(self):
        with mock.patch('popresearch.cmix.api.requests.post') as mock_post:
            mock_post_response = mock.Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                'response': 1,
                'error': 'Oops!',
            }
            mock_post.return_value = mock_post_response
            with mock.patch('popresearch.cmix.api.requests.get') as mock_get:
                # Check CmixError is raised if POST response JSON includes an error.
                mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Default',
                }]
                mock_get.return_value = mock_response
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.cmix_survey, 'XLSX_READABLE')

            # Remove error from POST response.
            mock_post_response.json.return_value = {'response': 1}

            with mock.patch('popresearch.cmix.api.requests.get') as mock_get:
                # Check CmixError is raised on GET 500 response. (layout response)
                mock_response = mock.Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Default',
                }]
                mock_get.return_value = mock_response
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.cmix_survey, 'XLSX_READABLE')

                # Check CmixError is raised if no default layout is returned.
                mock_response.status_code = 200
                mock_response.json.return_value = [{
                    'id': 1,
                    'name': 'Not Default',
                }]
                with self.assertRaises(CmixError):
                    self.cmix_api.create_export_archive(self.cmix_survey, 'XLSX_READABLE')

    def test_get_survey_status(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}

        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {'status': 'LIVE'}
            mock_request.get.return_value = mock_get

            self.assertEqual(self.cmix_api.get_survey_status(self.cmix_survey.id), 'live')

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            surveys_url = '{}/surveys/{}'.format(base_url, self.cmix_survey.id)
            mock_request.get.assert_any_call(surveys_url, headers=self.cmix_api._authentication_headers)

    def test_get_survey_status_error_handled(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}

        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                self.cmix_api.get_survey_status(self.cmix_survey.id)

    def test_get_survey_test_url(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}
        correct_test_link = '{}/#/?cmixSvy={}&cmixTest={}'.format(
            CMIX_SERVICES['test']['BASE_URL'], self.cmix_survey.id, 'test')

        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {'testToken': 'test'}
            mock_request.get.return_value = mock_get

            self.assertEqual(self.cmix_api.get_survey_test_url(self.cmix_survey.id), correct_test_link)

    def test_get_survey_test_url_no_token_handled(self):
        self.cmix_api._authentication_headers = {'Authentication': 'Bearer test'}
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                self.cmix_api.get_survey_test_url(self.cmix_survey.id)

    def test_get_survey_completes(self):
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
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
            self.assertEqual(self.cmix_api.get_survey_completes(self.cmix_survey.id), mock_respondents)

    def test_get_surveys(self):
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
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
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
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
            self.cmix_api.fetch_banner_filter(self.cmix_survey.id, question_a, question_b, response_id)
            expected_url = '{}/surveys/{}/response-counts'.format(
                CMIX_SERVICES['reporting']['BASE_URL'], self.cmix_survey.id)
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

    def test_update_archive_status(self):
        cda = CmixDataArchive.objects.create(
            cmix_survey_id=self.cmix_survey.id,
            json={'dataLayoutId': 1, 'id': 2}
        )
        with mock.patch('popresearch.cmix.api.requests.get') as mock_request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'COMPLETE',
                'archiveUrl': 'http://popresearch.com/',
            }

            mock_request.return_value = mock_response
            self.cmix_api.update_archive_status(cda)
        self.assertEqual(cda.status, CmixDataArchive.PROCESSED)
        self.assertEqual(cda.download_url, 'http://popresearch.com/')

        with mock.patch('popresearch.cmix.api.requests.get') as mock_request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'COMPLETE',
                'archiveUrl': 'http://popresearch.com/',
            }
            mock_request.return_value = mock_response

            with self.assertRaises(CmixError):
                cda.json = {}
                cda.save()
                self.cmix_api.update_archive_status(cda)

            with self.assertRaises(CmixError):
                cda.json = {'dataLayoutId': 1}
                cda.save()
                self.cmix_api.update_archive_status(cda)

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

    def test_comparisonpop_survey_creation(self):
        self.maxDiff = None
        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_comparison.json', "r") as json_data_file:
            survey_json = json.load(json_data_file)
            comparison_survey = Survey.objects.create(
                user=self.user, name="ComparisonPop with Creative United States No Creative",
                survey_type=SURVEY_TYPE_COMPARISON, json=survey_json)
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_post = mock.Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                'id': '100',
                'response': '1',
                'token_type': 'test',
                'access_token': 'test',
            }
            mock_request.post.return_value = mock_post
            self.cmix_api.create_survey(comparison_survey)
            # (2 Test Cells + 1 Control Cell) * (2 Geographies) = 6

            self.assertEqual(CmixSurvey.objects.filter(survey=comparison_survey).count(), 6)

    def test_fail_survey_creation_quits_after_10_fails(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_creativepop_no_ameritest.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            creativepop_survey = Survey.objects.create(
                user=self.user, name="CreativePop to mock fail", survey_type=SURVEY_TYPE_CREATIVE, json=survey_json)
        with mock.patch('popresearch.cmix.api.requests') as mock_request:
            mock_post = mock.Mock()
            mock_post.status_code = 500
            mock_post.json.return_value = {
                'id': '100',
                'response': '1',
                'token_type': 'test',
                'access_token': 'test',
            }
            mock_request.post.return_value = mock_post
            for i in range(1, 11):
                try:
                    self.cmix_api.create_survey(creativepop_survey)
                except Exception:
                    "Failure throws an exception we're ignoring here."
                self.assertEqual(CmixSurvey.objects.filter(survey=creativepop_survey).count(), 0)
                self.assertEqual(Survey.objects.filter(id=creativepop_survey.id)[0].failed_creation_attempts, i)

            # After 10 tries it won't try try, and thus won't fail and won't throw an error
            self.cmix_api.create_survey(creativepop_survey)
            self.assertEqual(Survey.objects.filter(id=creativepop_survey.id)[0].failed_creation_attempts, 10)


class TestCmixParsing(TestCase):
    def setUp(self):
        self.user = UserFactory.create_safe()
        self.formatter = xmlformatter.Formatter(indent="1", indent_char="  ", encoding_output="UTF-8", preserve=["literal"])

        with open('backend/apps/popresearch/tests/test_files/cmix/test_custompop_survey.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.creative_survey = SurveyFactory.create(
                user=self.user, survey_type=SURVEY_TYPE_CUSTOM, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_creativepop_POP-2044.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.creative_survey_2044 = SurveyFactory.create(
                name="CreativePop for POP-2044", user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_creativepop_POP-2158.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.creative_survey_2158 = SurveyFactory.create(
                name="CreativePop for POP-2158", user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.forcedexposure_survey = SurveyFactory.create(
                name="ForcedExposure XML Test", user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE, json=survey_json, status=Survey.COMPLETED)

        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_with_language.json',
                "r") as data_file:
            survey_json = json.load(data_file)
            self.forcedexposure_survey_with_language = SurveyFactory.create(
                name="ForcedExposure XML with Language Test", user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_comparison.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.comparison_survey = SurveyFactory.create(
                name="ComparsionPop With Creative", user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_trackingpop.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.trackingpop_survey = SurveyFactory.create(
                name="TrackingPop Survey", user=self.user,
                survey_type=SURVEY_TYPE_TRACKING, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_trackingpop_no_ads.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.trackingpop_survey_no_ads = SurveyFactory.create(
                name="TrackingPop No Ads", user=self.user,
                survey_type=SURVEY_TYPE_TRACKING, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_trackingpop_with_ads.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.trackingpop_survey_with_ads = SurveyFactory.create(
                name="TrackingPop With Ads", user=self.user,
                survey_type=SURVEY_TYPE_TRACKING, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_comparison_no_creative.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.comparison_survey_no_creative = SurveyFactory.create(
                name="ComparsionPop Without Creative",
                user=self.user,
                survey_type=SURVEY_TYPE_CREATIVE,
                json=survey_json,
                status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_design_logo.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.designpop_survey_logo = SurveyFactory.create(
                name="DesignPop Logo",
                user=self.user,
                survey_type=SURVEY_TYPE_DESIGN,
                json=survey_json,
                status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_design_packaging.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.designpop_survey_packaging = SurveyFactory.create(
                name="DesignPop Packaging",
                user=self.user,
                survey_type=SURVEY_TYPE_DESIGN,
                json=survey_json,
                status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_design_naming.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.designpop_survey_naming = SurveyFactory.create(
                name="DesignPop Naming",
                user=self.user,
                survey_type=SURVEY_TYPE_DESIGN,
                json=survey_json,
                status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_design_tagline.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.designpop_survey_tagline = SurveyFactory.create(
                name="DesignPop Tagline",
                user=self.user,
                survey_type=SURVEY_TYPE_DESIGN,
                json=survey_json,
                status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_instantpop.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.instantpop_survey = SurveyFactory.create(
                name="InstantPop", user=self.user, survey_type=SURVEY_TYPE_INSTANT, json=survey_json, status=Survey.COMPLETED)

        with open('backend/apps/popresearch/tests/test_files/cmix/json/survey_custompop_POP-2214.json', "r") as data_file:
            survey_json = json.load(data_file)
            self.custompop_survey_shuffle_none = SurveyFactory.create(
                name="POP-2214",
                user=self.user,
                survey_type=SURVEY_TYPE_CUSTOM,
                json=survey_json,
                status=Survey.COMPLETED)

    def helper_compare_xml_vs_expected(self, json_filename, test_function, expected_soup_filename):
        with open('backend/apps/popresearch/tests/test_files/cmix/json/{}'.format(json_filename), 'r') as data_file:
            loaded_json = json.load(data_file)
            generated_xml = test_function(loaded_json)
            generated_xml = ElementTree.tostring(generated_xml)
            generated_xml = self.formatter.format_string(generated_xml)
            generated_lines = generated_xml.splitlines()

        with open('backend/apps/popresearch/tests/test_files/cmix/xml/{}'.format(expected_soup_filename), "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()

        self.helper_compare_lines(generated_lines, expected_lines)

    def helper_compare_lines(self, lines1, lines2):
        self.assertEqual(len(lines1), len(lines2))
        for line_index, line in enumerate(lines1):
            try:
                self.assertEqual(lines1[line_index], lines2[line_index])
            except AssertionError:
                print("*" * 80)
                print()
                print(lines1[line_index])
                print()
                print(lines2[line_index])
                print("*" * 80)
                raise AssertionError("Line mismatch, line {}".format(line_index))

    def test_helper_compare_lines(self):
        lines_1 = ["hello", "world"]
        lines_2 = ["hello", "foo"]
        lines_3 = ["hello"]
        with self.assertRaises(AssertionError):
            self.helper_compare_lines(lines_1, lines_2)
        with self.assertRaises(AssertionError):
            self.helper_compare_lines(lines_1, lines_3)

    def test_create_numeric_question_page(self):
        self.helper_compare_xml_vs_expected('numeric_question.json', create_question_page, 'numeric_question.xml')

    def test_create_numeric_question_with_answer_ranges_page(self):
        self.helper_compare_xml_vs_expected(
            'numeric_question_with_answer_ranges.json', create_question_page, 'numeric_question_with_answer_ranges.xml')

    def test_numeric_question_with_anchoring(self):
        self.helper_compare_xml_vs_expected(
            'numeric_question_with_anchoring.json', create_question_page, 'numeric_question_with_anchoring.xml')

    def test_create_rating_grid_question_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected('rating_grid_question.json', create_question_page, 'rating_grid_question.xml')

    def test_create_vertical_radio_grid_question_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected(
            'vertical_radio_grid_question.json', create_question_page, 'vertical_radio_grid_question.xml')

    def test_create_horizontal_grid_question_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected(
            'horizontal_radio_grid_question.json', create_question_page, 'horizontal_radio_grid_question.xml')

    def test_create_checkbox_grid_question_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected('checkbox_grid_question.json', create_question_page, 'checkbox_grid_question.xml')

    def test_create_radio_question_page(self):
        self.helper_compare_xml_vs_expected('radio_question.json', create_question_page, 'radio_question.xml')

    def test_create_checkbox_question_page(self):
        self.helper_compare_xml_vs_expected('checkbox_question.json', create_question_page, 'checkbox_question.xml')

    def test_create_checkbox_question_with_types_page(self):
        self.helper_compare_xml_vs_expected(
            'checkbox_question_with_types.json', create_question_page, 'checkbox_question_with_types.xml')

    def test_create_checkbox_with_shuffle_question_page(self):
        self.helper_compare_xml_vs_expected(
            'checkbox_question_shuffle.json', create_question_page, 'checkbox_question_shuffle.xml')

    def test_create_checkbox_question_exclusive_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected(
            'checkbox_question_exclusive.json', create_question_page, 'checkbox_question_exclusive.xml')

    def test_create_checkbox_question_exclusive_no_ordering_page(self):
        self.maxDiff = None
        self.helper_compare_xml_vs_expected(
            'checkbox_question_exclusive_no_ordering.json',
            create_question_page,
            'checkbox_question_exclusive_no_ordering.xml'
        )

    def test_create_text_question_page(self):
        self.helper_compare_xml_vs_expected('text_question.json', create_question_page, 'text_question.xml')

    def test_create_none_question_page(self):
        self.helper_compare_xml_vs_expected('none_question.json', create_question_page, 'none_question.xml')

    def test_page_logic(self):
        self.maxDiff = None
        question = {
            'name': 'Q5',
            'page_logic': [
                {'block_type': 'block', 'condition': 'Q5 = 1', 'actions': [
                    {'type': 'goToQuestion', 'name': 'Q6'}
                ]},
                {'block_type': 'block', 'condition': 'AD_SEEN > 2', 'actions': [
                    {'type': 'terminate', 'name': 'AD_NOT_SEEN'}
                ]},
                {'block_type': 'block', 'actions': [
                    {'type': 'setVariable', 'name': 'AD_SEEN', 'formula': 'AD_SEEN + 1'},
                    {'type': 'clearQuestion', 'name': 'Q5'},
                    {'type': 'goToQuestion', 'name': 'SHOW_AD_VIDEO'},
                ]},
                {'block_type': 'loop', 'loop_variable': 'BRANDS', 'actions': [
                    {'block_type': 'block', 'condition': 'Q1 = 1', 'actions': [
                        {'type': 'terminate', 'name': 'TERM_QUOTA'}
                    ]},
                    {'block_type': 'block', 'condition': 'Q3 = 1', 'actions': [
                        {'type': 'goToQuestion', 'name': 'Q1'},
                        {'type': 'setVariable', 'name': 'AD_SEEN', 'to-response': '1'}
                    ]},
                ]},
            ]
        }
        logic_xml = ElementTree.tostring(create_page_logic(question))
        logic_soup = BeautifulSoup(logic_xml, 'html.parser')
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/pagelogic.xml', "r") as data_file:
            expected_soup = BeautifulSoup(data_file, 'html.parser')

        self.assertEqual(
            unicode(logic_soup).replace('\n', '').replace('&gt;', '>'),
            unicode(expected_soup).replace('\n', '').replace('&gt;', '>')
        )

    def test_create_legacy_concept(self):
        self.helper_compare_xml_vs_expected('legacy_concept.json', create_legacy_concept, 'legacy_concept.xml')

    def test_demographics_section(self):
        self.maxDiff = None
        demo_xml = ElementTree.tostring(create_demographic_questions_section(self.creative_survey))
        demo_xml = self.formatter.format_string(demo_xml)
        demo_lines = demo_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/demographics_section.xml', "w") as data_file:
        #    data_file.write(demo_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/demographics_section.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(demo_lines, expected_lines)

    def test_create_media_page(self):
        self.maxDiff = None
        page_xml = ElementTree.tostring(create_media_page({
            "url":
            "https://popresearch.s3.amazonaws.com/userData/uploads/ryqcsw6nb-Fast%20Food_KFC_Lieutenant%20Col.%20Cooks.jpg",
            "brand": "KFC",
            "filename": "Fast Food_KFC_Lieutenant Col. Cooks.jpg",
            "ad_name": "Lieutenant Col",
            "name": "C1",
            "type": "image/jpeg",
            "id": "cj8p176fm00203k7koipe8558"
        }))
        page_soup = BeautifulSoup(page_xml, 'html.parser')
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/media_page.xml', "r") as data_file:
            expected_soup = BeautifulSoup(data_file, 'html.parser')

        self.assertEqual(unicode(page_soup).replace('\n', ''), unicode(expected_soup).replace('\n', ''))

    def test_custompop_markup(self):
        generated_xml = generate_survey_xml(self.creative_survey)
        dumped_xml = ElementTree.tostring(generated_xml)
        soup = BeautifulSoup(dumped_xml, 'xml')
        survey_element = soup.find_all('survey')[0]

        # Ensure there's only one survey generated.
        self.assertEqual(len(soup.find_all('survey')), 1)

        # 2 sections: Custom Questions, Demographics
        self.assertEqual(len(survey_element.find_all('section')), 2)

        custom_question_section = survey_element.find_all('section')[0]
        # 1 introduction page + 4 custom questions
        self.assertEqual(len(custom_question_section.find_all('page')), 5)

        # 9 Demographic Questions
        demo_section = survey_element.find_all('section')[1]
        self.assertEqual(len(demo_section.find_all('page')), 9)

    @freeze_time("2001-01-01 00:00:00")
    def test_creativepop_markup_2044(self):
        self.maxDiff = None
        generated_xml = generate_survey_xml_strings_and_secondary_keys(self.creative_survey_2044)[0][1]
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_creativepop_POP-2044.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_creativepop_POP-2044.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_creativepop_markup_2158(self):
        self.maxDiff = None
        generated_xml = generate_survey_xml_strings_and_secondary_keys(self.creative_survey_2158)[0][1]
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_creativepop_POP-2158.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_creativepop_POP-2158.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_cell.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey(
                name="ForcedExposure Survey Test Curry",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
        generated_xml = generate_survey_xml_string(forcedexposure_survey_cell)
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_cell.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_cell.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup_cell_keys(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey(
                name="ForcedExposure Survey Test Curry",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(forcedexposure_survey_cell)
        self.assertEqual(len(strings_and_keys), 7)  # 7 cells
        generated_key = strings_and_keys[0][0]
        self.assertEqual(generated_key, '0-Custom Geography')

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_cell_with_language(self):
        self.maxDiff = None
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_cell_french.json',
                mode="r",
                encoding="utf-8") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey(
                name="ForcedExposure Survey Test Curry",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
        generated_xml = generate_survey_xml_string(forcedexposure_survey_cell)
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_french.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_french.xml',
                mode="r",
                encoding="utf-8") as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup_with_language(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_with_language.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey.objects.create(
                user=self.user, name="ForcedExposure Language Test",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
            forcedexposure_survey_cell.id = 6
            forcedexposure_survey_cell.save()

        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(forcedexposure_survey_cell)
        self.assertEqual(len(strings_and_keys), 14)  # 7 cells * 2 countries * 1 language
        generated_key = strings_and_keys[0][0]
        generated_xml = strings_and_keys[0][1]
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        self.assertEqual(generated_key, '0-United States')
        # with open(
        #        'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_with_language_united_states.xml',
        #        "w") as data_file:
        #    data_file.write(generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_with_language_united_states.xml',
                mode="r",
                encoding="utf-8") as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

        second_cell_generated_key = strings_and_keys[1][0]
        second_cell_generated_xml = strings_and_keys[1][1]
        second_cell_generated_xml = self.formatter.format_string(second_cell_generated_xml.encode('utf-8'))
        second_cell_generated_lines = second_cell_generated_xml.splitlines()
        self.assertEqual(second_cell_generated_key, '0-Japan')
        # with open(
        #        'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_with_language_japan.xml',
        #        "w") as data_file:
        #    data_file.write(second_cell_generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_with_language_japan.xml',
                mode="r",
                encoding="utf-8") as data_file:
            second_cell_expected_xml = data_file.read().encode('utf-8')
        second_cell_expected_lines = second_cell_expected_xml.splitlines()
        self.helper_compare_lines(second_cell_generated_lines, second_cell_expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup_norwegian(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_norwegian.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey.objects.create(
                user=self.user,
                name="ForcedExposure Norwegian Language Test",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
            forcedexposure_survey_cell.id = 6
            forcedexposure_survey_cell.save()

        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(forcedexposure_survey_cell)
        self.assertEqual(len(strings_and_keys), 2)  # 2 cells * 1 country * 1 language
        generated_key = strings_and_keys[0][0]
        generated_xml = strings_and_keys[0][1]
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        self.assertEqual(generated_key, '0-United States')
        # with open(
        #        'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_no_united_states.xml',
        #        "w") as data_file:
        #    data_file.write(generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_no_united_states.xml',
                mode="r",
                encoding="utf-8") as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup_portuguese(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_portuguese.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey.objects.create(
                user=self.user,
                name="ForcedExposure Portuguese Language Test",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
            forcedexposure_survey_cell.id = 6
            forcedexposure_survey_cell.save()

        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(forcedexposure_survey_cell)
        self.assertEqual(len(strings_and_keys), 2)  # 2 cells * 1 country * 1 language
        generated_key = strings_and_keys[0][0]
        generated_xml = strings_and_keys[0][1]
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        self.assertEqual(generated_key, '0-United States')
        # with open(
        #        'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_pt_united_states.xml',
        #        "w") as data_file:
        #    data_file.write(generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_pt_united_states.xml',
                mode="r",
                encoding="utf-8") as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_forcedexposure_markup_spanish(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_forcedexposure_spanish.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            forcedexposure_survey_cell = Survey.objects.create(
                user=self.user,
                name="ForcedExposure Spanish Language Test",
                survey_type=SURVEY_TYPE_FORCEDEXPOSURE,
                json=survey_json
            )
            forcedexposure_survey_cell.id = 6
            forcedexposure_survey_cell.save()

        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(forcedexposure_survey_cell)
        self.assertEqual(len(strings_and_keys), 2)  # 2 cells * 1 country * 1 language
        generated_key = strings_and_keys[0][0]
        generated_xml = strings_and_keys[0][1]
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        self.assertEqual(generated_key, '0-United States')
        # with open(
        #        'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_es_united_states.xml',
        #        "w") as data_file:
        #    data_file.write(generated_xml)
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_forcedexposure_es_united_states.xml',
                mode="r",
                encoding="utf-8") as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_comparisonpop_markup(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_comparison_cell.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            comparison_survey_cell = Survey(
                name="ComparisonPop with Creative United States Pop Logo",
                survey_type=SURVEY_TYPE_COMPARISON,
                json=survey_json
            )
        generated_xml = generate_survey_xml_string(comparison_survey_cell)
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_comparison.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_comparison.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_comparisonpop_markup_no_creative(self):
        self.maxDiff = None
        with open(
                'backend/apps/popresearch/tests/test_files/cmix/json/survey_comparison_cell_no_creative.json',
                "r") as json_data_file:
            survey_json = json.load(json_data_file)
            comparison_survey_cell = Survey(
                name="ComparisonPop with Creative United States No Creative",
                survey_type=SURVEY_TYPE_COMPARISON,
                json=survey_json
            )
        generated_xml = generate_survey_xml_string(comparison_survey_cell)
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_comparison_no_creative.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_comparison_no_creative.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_trackingpop_markup_no_ads(self):
        self.maxDiff = None
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(self.trackingpop_survey)
        generated_key = strings_and_keys[0][0]
        self.assertEqual(generated_key, '0')
        generated_xml = strings_and_keys[0][1]
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_trackingpop_no_ads.xml',
                "r",
                encoding='utf8') as data_file:
            expected_xml = data_file.read().encode('utf-8')
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_trackingpop_markup_with_ads(self):
        self.maxDiff = None
        generated_xml = generate_survey_xml_string(self.trackingpop_survey_with_ads)
        generated_xml = self.formatter.format_string(generated_xml)
        generated_lines = generated_xml.splitlines()
        with io.open(
                'backend/apps/popresearch/tests/test_files/cmix/xml/survey_trackingpop_with_ads.xml',
                "r",
                encoding='utf8') as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_designpop_survey_logo(self):
        self.maxDiff = None
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(self.designpop_survey_logo)
        self.assertEqual(len(strings_and_keys), 2)  # 1 Stimulus, 1 Test
        generated_xml = self.formatter.format_string(strings_and_keys[0][1].encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_logo.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_logo.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_designpop_survey_packaging(self):
        self.maxDiff = None
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(self.designpop_survey_packaging)
        self.assertEqual(len(strings_and_keys), 2)  # 1 Stimulus, 1 Test
        generated_xml = self.formatter.format_string(strings_and_keys[0][1].encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_packaging.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_packaging.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_designpop_survey_naming(self):
        self.maxDiff = None
        generated_xml = generate_survey_xml_string(self.designpop_survey_naming)
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_naming.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_naming.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_designpop_survey_tagline(self):
        self.maxDiff = None
        generated_xml = generate_survey_xml_string(self.designpop_survey_tagline)
        generated_xml = self.formatter.format_string(generated_xml.encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_tagline.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_design_tagline.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_instantpop_markup(self):
        self.maxDiff = None
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(self.instantpop_survey)
        generated_xml = self.formatter.format_string(strings_and_keys[0][1].encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_instantpop.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_instantpop.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)

    @freeze_time("2001-01-01 00:00:00")
    def test_answer_shuffle_none(self):
        self.maxDiff = None
        strings_and_keys = generate_survey_xml_strings_and_secondary_keys(self.custompop_survey_shuffle_none)
        generated_xml = self.formatter.format_string(strings_and_keys[0][1].encode('utf-8'))
        generated_lines = generated_xml.splitlines()
        # with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_custompop_POP-2214.xml', "w") as data_file:
        #    data_file.write(generated_xml)
        with open('backend/apps/popresearch/tests/test_files/cmix/xml/survey_custompop_POP-2214.xml', "r") as data_file:
            expected_xml = data_file.read()
        expected_lines = expected_xml.splitlines()
        self.helper_compare_lines(generated_lines, expected_lines)
