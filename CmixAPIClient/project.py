# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .error import CmixError


class CmixProject(object):
    def __init__(self, client, project_id):
        if None in [client, project_id]:
            raise CmixError("Client and project id are required.")
        self.client = client
        self.project_id = project_id

    def delete_project(self):
        project_endpoint = 'projects/{}'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while deleting project'
        project_response = self.client.api_delete(project_endpoint, project_error)
        return project_response

    def delete_group(self, group_id):
        project_endpoint = 'projects/{}/groups/{}'.format(self.project_id, group_id)
        project_error = 'CMIX returned a non-200 response code while deleting group'
        project_response = self.client.api_delete(project_endpoint, project_error)
        return project_response

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

    def get_groups(self):
        project_endpoint = 'projects/{}/groups'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project groups'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_links(self):
        project_endpoint = 'projects/{}/links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_full_links(self):
        project_endpoint = 'projects/{}/full-links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project full links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_locales(self):
        project_endpoint = 'projects/{}/locales'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project locales'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_markup_files(self):
        project_endpoint = 'projects/{}/markup-files'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project markup files'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_respondent_links(self):
        project_endpoint = 'projects/{}/respondent-links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project respondent links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_surveys(self):
        project_endpoint = 'projects/{}/surveys'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project surveys'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response
