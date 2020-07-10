-----------

Release 0.1.3 (released January 23, 2020)
============================================

* Refactored get methodology in ``CmixAPIClient`` for use by ``CMixProject`` functions
* Created delete method in ``CmixAPIClient`` for use by ``CMixProject`` functions
* Added functions to ``CmixAPIClient``:

  .. code-block:: python
  
    get_projects()
    get_survey_data_layouts(survey_id)
    get_survey_locales(survey_id)
    get_survey_sections(survey_id)
    get_survey_simulations(survey_id)
    get_survey_termination_codes(survey_id)
    get_survey_sources(survey_id)

* Created a ``CMixProject`` class and added functions:

  .. code-block:: python

    CmixProject.delete_group(group_id)
    CmixProject.delete_project()
    CmixProject.get_full_links()
    CmixProject.get_groups()
    CmixProject.get_links()
    CmixProject.get_locales()
    CmixProject.get_markup_files()
    CmixProject.get_project()
    CmixProject.get_respondent_links()
    CmixProject.get_sources()
    CmixProject.get_surveys()
