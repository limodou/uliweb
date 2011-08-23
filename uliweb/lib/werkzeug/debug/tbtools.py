# -*- coding: utf-8 -*-
"""
    werkzeug.debug.tbtools
    ~~~~~~~~~~~~~~~~~~~~~~

    This module provides various traceback related utility functions.

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD.
"""
import re
import os
import sys
import inspect
import traceback
import codecs
from tokenize import TokenError

_coding_re = re.compile(r'coding[:=]\s*([-\w.]+)')
_line_re = re.compile(r'^(.*?)$(?m)')
_funcdef_re = re.compile(r'^(\s*def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')
UTF8_COOKIE = '\xef\xbb\xbf'

system_exceptions = (SystemExit, KeyboardInterrupt)
try:
    system_exceptions += (GeneratorExit,)
except NameError:
    pass


def get_current_traceback(ignore_system_exceptions=False):
    """Get the current exception info as `Traceback` object.  Per default
    calling this method will reraise system exceptions such as generator exit,
    system exit or others.  This behavior can be disabled by passing `False`
    to the function as first parameter.
    """
    exc_type, exc_value, tb = sys.exc_info()
    if ignore_system_exceptions and exc_type in system_exceptions:
        raise
    return Traceback(exc_type, exc_value, tb)

class Traceback(object):
    """Wraps a traceback."""

    def __init__(self, exc_type, exc_value, tb):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb

    @property
    def plaintext(self):
        return ''.join(traceback.format_exception(self.exc_type, self.exc_value, self.tb))
