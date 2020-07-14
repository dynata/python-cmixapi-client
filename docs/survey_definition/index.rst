.. This is based off of the documentation available at:
   https://wiki2.criticalmix.net/display/CA/CMIX+Survey+Markup+Format+Specification

#############################
The Survey Definition
#############################

.. tip::

  This documentation for the **Dynata Survey Definition** format is only partial.
  We are working to expand it to include the full set of documentation, but in
  the meantime we recommend you review the work-in-progress documentation
  available here:
  https://wiki2.criticalmix.net/display/CA/CMIX+Survey+Markup+Format+Specification

.. sidebar:: XML or Not-XML?

  The Dynata Survey Definition is not -- strictly speaking -- an XML file. XML
  is designed to be a strict and unforgiving language. HTML, which is what
  surveys are ultimately rendered in, has been designed over the years to
  naturally be more forgiving than the XML standard.

  By trying to maintain some level of consistency with the standards of
  `HTML Custom Elements <https://w3c.github.io/webcomponents/spec/custom/>`_,
  the Dynata Survey Definition format gains several advantages over native XML:

  * It is inherently more forgiving (e.g. can support unclosed tags).
  * It enables the re-use of HTML tags to simplify browser-based-rendering.
  * It allows for compatibility with standards-complaint technologies like
    `Web Components <https://en.wikipedia.org/wiki/Web_Components>`_ and
    JavaScript-based component-based frameworks (e.g.
    `Angular <https://angular.io/>`_ or React).

.. contents::
  :depth: 3
  :backlinks: entry

--------------

*********************************
What is a Survey Definition?
*********************************

The :term:`Survey Definition` is the "source code" for the survey you create
using the Dynata Survey Authoring tool (Cmix). It controls:

  * what questions your survey contains
  * how those questions are arranged
  * how the survey respondent navigates between those questions
  * how those questions map to variables / data

As such, your survey definition is literally the "heart" of your survey. It can
be defined and modified using a number of different tools:

  * **Dynata Survey Authoring (Cmix)**. One of the key advantages of the
    Dynata Survey Authoring tool is that it allows you to use an easy-to-use
    point-and-click system to create and modify your surveys.
  * **Text Editor / IDE**. Because the survey definition can be exported out of the
    tool itself and accessed via the Dynata Survey Authoring API, you can also
    modify it using any text editor or IDE (Integrated Development Environment).

    .. caution::

      This is a technique for advanced users.

  * **Programmatically**. Because the survey definition is a machine-readable
    format, it is possible for your systems to automatically create or modify
    survey definition files and deliver them to the tool using the Dynata Survey
    Authoring API.

-------------------

***********************************************
High-level Structure of a Survey Definition
***********************************************

At a high level, a :term:`Survey Definition` is composed of a number of "simple"
building blocks:

* :ref:`Survey <survey_element>`. Unsurprisingly, this is the starting point for
  the definition. Everything within the survey definition has to correspond to
  the single definition of the survey itself.
* :ref:`Sections <section_element>`. Each survey is composed of one or more
  sections, where each section is a logical group of multiple
  :ref:`pages <page_element>`.
* :ref:`Logic Block <logic_block_element>` (optional). Each section can include
  one or more blocks of logic which perform a variety of evaluations and determine
  how to direct the respondent based on those evaluations.
* :ref:`Pages <page_element>`. Each section is composed of one or more pages,
  where each page is a single "view" that is shown to a respondent when taking
  the survey. This view is itself composed of :ref:`questions <question_element>`.
* :ref:`Questions <question_element>`. Each page is composed of one or more
  questions, where each question is a survey question that is asked of a
  respondent taking the survey.

.. todo::

  Add a diagram showing this structure.

Besides these basic building blocks, there are a number of additional pieces
that are used to build more advanced structures and logic, including:

* :ref:`Concepts <concept_element>` which are used to define concept variables
  which can be reused across the survey.
* :ref:`Lists <list_element>` which are used to define response lists which can
  be reused across multiple survey questions.
* :ref:`Termination Codes <term_code_element>` which are used to define the
  different termination codes which are used to demarcate a respondent as having
  terminated a survey prior to completion.
* :ref:`Variables <variable_element>` which are used to define variables that
  can be populated through the survey, its logic, or populated by the
  :term:`sample source <Sample Source>`.

--------------------------

************************
Basic Building Blocks
************************

.. _survey_element:

Survey Element
=================

The ``<survey>`` element represents a survey in its entirety.  This element
should be the root of the survey definition (i.e. the ancestor of all other
elements).

  .. note::

    * **MUST** be the first / highest-level element in the survey definition.
    * One survey definition **CANNOT** have more than one ``<survey>`` element.


Attributes
-------------

  .. py:attribute:: name
    :type: string
    :value: "My Survey"
    :noindex:

     **REQUIRED**. Human-readable name given to the survey.

Example
------------

  .. code-block:: xml

    <survey name="My Survey">
      ...
    </survey>

-------------

.. _section_element:

Section Element
===================

.. sidebar:: Parent Elements

  * :ref:`survey <survey_element>`

The ``<section>`` element defines a section, which is a collection of one or
more :ref:`pages <page_element>` or :ref:`logic blocks <logic_block_element>`.

  .. note::

    * One survey definition **CAN** have multiple ``<section>`` elements.

  .. caution::

    Do not confuse a ``<section>`` element with the HTML
    `section tag <https://html.spec.whatwg.org/multipage/sections.html#the-section-element>`_
    which serves a different purpose.

Attributes
------------------

  .. py:attribute:: label
    :type: string
    :value: "My Section"
    :noindex:

    Human-readable label given to the section. This label is not shown to
    respondents, but will be visible within the Dynata Survey Authoring system.

  .. py:attribute:: loop
    :type: string
    :value: "concept_1"
    :noindex:

    Machine-readable name of a :ref:`concept <concept_element>` the section is
    associated with in a :ref:`loops <survey_loops>`.

Example
---------------

  .. tabs::

    .. tab:: Standard

      .. code-block:: xml

        <survey name="My Survey">
          <section label="My First Section">
            ...
          </section>
          ...
        </survey>

    .. tab:: With Loop

      .. code-block:: xml

        <survey name="My Survey">
          <section loop="MyConceptLoop">
            ...
          </section>
          ...
        </survey>

      .. seealso::

        * :ref:`Survey Loops Explained <managing_logic#survey_loops>`

-------------

.. _logic_block_element:

Logic Element
========================

.. sidebar:: Parent Elements

  * :ref:`section <section_element>`
  * :ref:`survey <survey_element>`

The ``<logic>`` element is used to define a set of logical evaluations and
decisions as to how to direct a respondent through the survey experience itself.

It is composed of either:

  * :ref:`blocks <block_element>` and/or
  * :ref:`loops <logic_loop_element>`

  .. seealso::

    * :doc:`Managing Survey Logic <managing_logic>`

Attributes
-------------

  .. py:attribute:: label
    :type: string
    :value: "My Logic Block"
    :noindex:

    A human-readable label that is applied to the logic block. This label is not
    shown to a respondent, but it will be the label shown in the Dynata Survey
    Authoring tool for the logic block.

  .. py:attribute:: variable
    :type: string
    :value: "concept_1"
    :noindex:

    If the logic block belongs within a loop, this is the loop concept that it
    belongs.

Example
-------------

  .. code-block:: xml

    <survey name="My Survey">
      <section label="My First Section">
        <logic label="My Logic Block" variable="concept_1">
          ...
        </logic>
        <logic label="My Second Logic Block">
          ...
        </logic>
      </section>
    </survey>

------------

.. _block_element:

Logic > Block Element
========================

  .. todo::

    Document this element.

------------

.. _logic_loop_element:

Logic > Loop Element
========================

  .. todo::

    Document this element.

------------

.. _page_element:

Page Element
========================

.. sidebar:: Parent Elements

  * :ref:`section <section_element>`

The ``<page>`` element is used to define a visual page, a single rendered
view that is shown to a respondent, which may contain one or more
:ref:`questions <question_element>`.

Attributes
--------------

  .. py:attribute:: label
    :type: string
    :value: "My Page"
    :noindex:

    A human-readable label that is applied to the page. This label will **not**
    be shown to a respondent, but will be shown in the Dynata Survey Authoring
    tool to aid in navigating your survey structure.

Example
-------------

  .. code-block:: xml

    <survey name="My Survey">
      <section label="My First Section">
        <page label="My First Page">
          ...
        </page>
        <page label="My Second Page">
          ...
        </page>
      </section>
    </survey>

-------------

.. _question_element:

Question Element
========================

.. sidebar:: Parent Elements

  * :ref:`page <page_element>`

Attributes
-------------

  .. tip::

    The attributes described below are the "standard" attributes that apply to
    every question type. However, each question type may have additional attributes
    that are used to configure its behavior and appearance in a more nuanced fashion.

    For more information, please see :doc:`Defining Survey Questions <questions>`.

  .. py:attribute:: name
    :type: string
    :value: "Q1"
    :noindex:

    **REQUIRED**. The machine-readable name given to the question.

  .. py:attribute:: type
    :type: string
    :value: "radio"
    :noindex:

    **REQUIRED**. Determines how the question should be rendered for a
    respondent. Accepts one of the following acceptable values:

      * ``radio``
      * ``check-box``
      * ``coordinate-tracker``
      * ``dragdrop-bucket``
      * ``dragdrop-scale``
      * ``dropdown``
      * ``highlight-image``
      * ``highlight-text``
      * ``numeric``
      * ``passcode``
      * ``pii``
      * ``radio``
      * ``real-answer``
      * ``scale``
      * ``simple-grid``
      * ``slider``
      * ``none``
      * ``text``

    .. seealso::

      * :doc:`Defining Survey Questions <questions>`

  .. py:attribute:: label
    :type: string
    :value: "Brand Awareness"
    :noindex:

    A human-readable label that will be shown for the question when viewing
    reports produced from the collected data.

  .. py:attribute:: required
    :type: Boolean
    :value: true
    :noindex:

    If ``true``, forces the respondent to provide an answer to the question.
    If ``false``, the respondent can proceed to the next question/step in the
    survey without supplying an answer.

  .. py:attribute:: skip
    :type: string
    :value: TBD
    :noindex:

    .. todo::

      Document the formula syntax.

    Accepts a formula that is automatically evaluated when the respondent
    reaches this question. If the formula evaluates to ``true``, then the
    question will be skipped.

  .. py:attribute:: parameter
    :type: string
    :value: "param1"
    :noindex:

    If present, will auto-populate this question with a value extracted from a
    URL parameter with the name supplied.

  .. py:attribute:: display
    :type: string
    :value: TBD
    :noindex:

    .. todo::

      * Document the formula syntax.
      * Document what this attribute does.

Examples
------------

  .. seealso::

    For detailed documentation on how to construct questions, please see
    :doc:`Defining Survey Questions <questions>`.
