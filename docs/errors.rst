##################################
Error Reference
##################################

.. module:: CmixAPIClient.error

.. contents::
  :local:
  :depth: 3
  :backlinks: entry

----------

*******************
Handling Errors
*******************

.. tip::

When functions within the library fail, they raise exceptions. There are three
ways for exceptions to provide you with information that is useful in different
circumstances:

#. **Exception Type**. The type of the exception itself (and the name of that type)
   tells you a lot about the nature of the error. On its own, this should be
   enough for you to understand "what went wrong" and "why validation failed".
   Most importantly, this is easy to catch in your code using ``try ... except``
   blocks, giving you fine-grained control over how to handle exceptional situations.
#. **Message**. Each exception is raised with a human-readable message, a brief
   string that says "this is why this exception was raised". This is primarily
   useful in debugging your code, because at run-time we don't want to parse
   strings to make control flow decisions.
#. **Stack Trace**. Each exception is raised with a stacktrace of the exceptions
   and calls that preceded it. This helps to provide the context for the error, and
   is (typically) most useful for debugging and logging purposes. In rare circumstances,
   we might want to programmatically parse this information...but that's a pretty
   rare requirement.

We have designed the exceptions raised by the **Dynata Survey Authoring** library
to leverage all three of these types of information.

Error Names/Types
===========================

By design, all exceptions raised by the **Dynata Survey Authoring** library
inherit from the `built-in exceptions <https://docs.python.org/3.6/library/exceptions.html>`_
defined in the standard library. This makes it simple to plug the
**Dynata Survey Authoring** library into existing code which already catches
:class:`ValueError <python:ValueError>`, :class:`TypeError <python:TypeError>`,
and the like.

However, because we have sub-classed the built-in exceptions, you can easily apply
more fine-grained control over your code.

.. tip::

  We **strongly** recommend that you review the exceptions raised by each of
  the functions you use. Each function precisely documents which exceptions it
  raises, and each exception's documentation shows what built-in exceptions it
  inherits from.

Error Messages
===========================

Because the **Dynata Survey Authoring** library produces exceptions which inherit
from the standard library, we leverage the same API. This means they print to
standard output with a human-readable message that provides an explanation for
"what went wrong."

Stack Traces
===========================

Because the **Dynata Survey Authoring** library produces exceptions which inherit
from the standard library, it leverages the same API for handling stack trace
information. This means that it will be handled just like a normal exception in
unit test frameworks, logging solutions, and other tools that might need that
information.

---------

*******************
Standard Errors
*******************

CmixError (from :class:`Exception <python:Exception>`)
==========================================================

.. autoclass:: CmixError
