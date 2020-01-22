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
            mock_request.get.assert_any_call(project_url, headers=self.cmix_api._authentication_headers)

        # error case (survey not found)
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 404
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                func()

    def test_get_project(self):
        self.helper_get('get_project', '/{}'.format(self.project_id))

    def test_get_sources(self):
        self.helper_get('get_sources', '/{}/sources'.format(self.project_id))

    def test_get_groups(self):
        self.helper_get('get_groups', '/{}/groups'.format(self.project_id))
