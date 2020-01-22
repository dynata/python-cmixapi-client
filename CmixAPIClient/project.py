# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .error import CmixError


class CmixProject(object):
    def __init__(self, client, project_id):
        if None in [client, project_id]:
            raise CmixError("Client and project id are required.")
        self.client = client
        self.project_id = project_id

    def get_project(self):
        project_endpoint = 'projects/{}'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_sources(self):
        project_endpoint = 'projects/{}/sources'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project sources'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response
