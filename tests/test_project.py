# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import mock

from unittest import TestCase
from CmixAPIClient.api import CMIX_SERVICES
from CmixAPIClient.project import CmixProject
from CmixAPIClient.error import CmixError
from .test_api import default_cmix_api


class TestCmixProject(TestCase):
    def setUp(self):
        self.cmix_api = default_cmix_api()
        self.cmix_api._authentication_headers = {'Authorization': 'Bearer test'}
        self.project_id = 1492

    def helper_get(self, function_name, endpoint):
        project = CmixProject(self.cmix_api, self.project_id)
        func = getattr(project, function_name)

        # success case
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            func()

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            project_url = '{}/projects{}'.format(base_url, endpoint)
            mock_request.get.assert_any_call(project_url, headers=self.cmix_api._authentication_headers, timeout=5)

        # error case (survey not found)
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 404
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                func()

    def helper_delete(self, function_name, endpoint, group_id=None):
        project = CmixProject(self.cmix_api, self.project_id)
        func = getattr(project, function_name)

        # success case
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_delete = mock.Mock()
            mock_delete.status_code = 200
            mock_delete.json.return_value = {}
            mock_request.delete.return_value = mock_delete

            if group_id is not None:
                func(group_id)
            else:
                func()

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            project_url = '{}/projects{}'.format(base_url, endpoint)
            mock_request.delete.assert_any_call(project_url, headers=self.cmix_api._authentication_headers, timeout=5)

        # error case (survey not found)
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_delete = mock.Mock()
            mock_delete.status_code = 404
            mock_delete.json.return_value = {}
            mock_request.delete.return_value = mock_delete

            with self.assertRaises(CmixError):
                if group_id is not None:
                    func(group_id)
                else:
                    func()

    def test_delete_group(self):
        self.helper_delete('delete_group', '/{}/groups/{}'.format(self.project_id, 13), 13)

    def test_delete_project(self):
        self.helper_delete('delete_project', '/{}'.format(self.project_id))

    def test_get_project(self):
        self.helper_get('get_project', '/{}'.format(self.project_id))

    def test_get_sources(self):
        self.helper_get('get_sources', '/{}/sources'.format(self.project_id))

    def test_get_groups(self):
        self.helper_get('get_groups', '/{}/groups'.format(self.project_id))

    def test_get_links(self):
        self.helper_get('get_links', '/{}/links'.format(self.project_id))

    def test_get_full_links(self):
        self.helper_get('get_full_links', '/{}/full-links'.format(self.project_id))

    def test_get_locales(self):
        self.helper_get('get_locales', '/{}/locales'.format(self.project_id))

    def test_get_markup_files(self):
        self.helper_get('get_markup_files', '/{}/markup-files'.format(self.project_id))

    def test_get_respondent_links(self):
        self.helper_get('get_respondent_links', '/{}/respondent-links'.format(self.project_id))

    def test_get_surveys(self):
        self.helper_get('get_surveys', '/{}/surveys'.format(self.project_id))
