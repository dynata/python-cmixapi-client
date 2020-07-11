# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .error import CmixError


class CmixProject(object):
    """An API client that exposes a variety of bindings for interacting with a
    given :term:`Project` defined on the Dynata Survey Authoring system.

    """
    def __init__(self, client, project_id):
        """
        :param client: An authenticated instance of the **Survey API Client**.
        :type client: :class:`CmixAPI <CmixAPIClient.api.CmixAPI>`

        :param project_id: The unique ID of the :term:`Project` to associate
          with this instance.
        :type project_id: :class:`int <python:int>`

        :raises CmixError: if either ``client`` or ``project_id`` are not
          supplied

        """
        if None in [client, project_id]:
            raise CmixError("Client and project id are required.")
        self.client = client
        self.project_id = project_id

    def delete_project(self):
        """Deletes the :term:`project <Project>` from the system.

        .. warning:: BE CAREFUL!

          This operation cannot be undone!

        :returns: The :class:`requests.Response <requests:requests.Response>` object for the API
          request
        :rtype: :class:`requests.Response <requests:requests.Response>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """

        project_endpoint = 'projects/{}'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while deleting project'
        project_response = self.client.api_delete(project_endpoint, project_error)
        return project_response

    def delete_group(self, group_id):
        """Deletes a :term:`Group` from the system.

        .. warning:: BE CAREFUL!

          This operation cannot be undone!

        :returns: The :class:`requests.Response <requests:requests.Response>` object for the API
          request
        :rtype: :class:`requests.Response <requests:requests.Response>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/groups/{}'.format(self.project_id, group_id)
        project_error = 'CMIX returned a non-200 response code while deleting group'
        project_response = self.client.api_delete(project_endpoint, project_error)
        return project_response

    def get_project(self):
        """Retrieves meta-data about the :term:`Project`.

        :returns: A :term:`Project` meta-data object represented as a
          :class:`dict <python:dict>` with keys:

          .. todo::

            Determine the keys returned.
        :rtype: :class:`dict <python:dict>`

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_sources(self):
        """Retrieve the sources for the :term:`project`.

        .. todo::

          Confirm that "project sources" means the sample sources.

        :returns: Collection of :term:`Survey Source` objects as
          :class:`dict <python:dict>` objects with keys:

          * ``id``: The unique ID of the :term:`Survey Source`
          * ``name``: The human-readable name of the :term:`Survey Source`
          * ``token``: TBD

          .. todo::

            Determine the meaning of the keys marked TBD

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/sources'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project sources'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_groups(self):
        """Retrieve :term:`Groups <Group>` defined for the :term:`project`.

        :returns: Collection of :term:`Group` objects as
          :class:`dict <python:dict>` objects with keys:

          .. todo::

            Determine the keys returned

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/groups'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project groups'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_links(self):
        """Retrieve :term:`Links` for the :term:`Project`.

        :returns: Collection of :term:`Link` objects as
          :class:`dict <python:dict>` objects with keys:

          .. todo::

            Determine the keys returned

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_full_links(self):
        """Retrieve :term:`Links` for the :term:`Project`.

        .. todo::

          What is the difference between this and ``get_links()`` ?

        :returns: Collection of :term:`Link` objects as
          :class:`dict <python:dict>` objects with keys:

          .. todo::

            Determine the keys returned

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/full-links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project full links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_locales(self):
        """Retrieve the :term:`locales <Locale>` defined for the :term:`Project`.

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
        project_endpoint = 'projects/{}/locales'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project locales'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_markup_files(self):
        """Retrieve the :term:`Markup Files` for the :term:`Project`.

        :returns: TBD

          .. todo::

            Determine what gets returned.

        :rtype: TBD

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/markup-files'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project markup files'
        project_response = self.client.api_get(project_endpoint, project_error)

        return project_response

    def get_respondent_links(self):
        """Retrieve the :term:`Respondent Links` for the :term:`Project`.

        :returns: Collection of :term:`Link` objects as
          :class:`dict <python:dict>` objects with keys:

          .. todo::

            Determine the keys returned

        :raises CmixError: if the API returns an HTTP Status Code other than ``200``

        """
        project_endpoint = 'projects/{}/respondent-links'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project respondent links'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response

    def get_surveys(self):
        """Retrieve surveys associated with the :term:`Project`.

        :returns: A collection of :term:`surveys <survey>` associated with the
          :term:`Project`, where each survey is represented as a
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
        project_endpoint = 'projects/{}/surveys'.format(self.project_id)
        project_error = 'CMIX returned a non-200 response code while getting project surveys'
        project_response = self.client.api_get(project_endpoint, project_error)
        return project_response
