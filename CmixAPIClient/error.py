# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class CmixError(Exception):
    '''
        This base error will help determine when CMIX returns a bad response or
        otherwise raises an exception while using the API.
    '''
    pass
