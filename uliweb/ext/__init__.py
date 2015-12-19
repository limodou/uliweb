# -*- coding: utf-8 -*-
from __future__ import absolute_import
"""
    uliweb.ext (modified from flask.ext)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    When a user does ``from uliweb.ext.foo import bar`` it will attempt to
    import ``from uliweb_foo import bar``.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


def setup():
    from ..utils.exthook import ExtensionImporter
    importer = ExtensionImporter(['uliweb_%s'], __name__)
    importer.install()


setup()
del setup