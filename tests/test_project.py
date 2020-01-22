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

    def test_get_project(self):
        project = CmixProject(self.cmix_api, self.project_id)

        # success case
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 200
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            project.get_project()

            base_url = CMIX_SERVICES['survey']['BASE_URL']
            project_url = '{}/projects/{}'.format(base_url, self.project_id)
            mock_request.get.assert_any_call(project_url, headers=self.cmix_api._authentication_headers)

        # error case (survey not found)
        with mock.patch('CmixAPIClient.api.requests') as mock_request:
            mock_get = mock.Mock()
            mock_get.status_code = 404
            mock_get.json.return_value = {}
            mock_request.get.return_value = mock_get

            with self.assertRaises(CmixError):
                project.get_project()
