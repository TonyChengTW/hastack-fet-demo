# Copyright (c) 2016 Fiberhome
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
gettext for HA service.

Usual usage in an openstack.common module:

    from hastack.has.stack import has_gettextutils
    _ = has_gettextutils._
"""

import gettext
import os

locale_path = os.path.join(os.path.dirname(__file__), 'locale')
t = gettext.translation('fit', locale_path, fallback=True)


def _(msg):
    return t.ugettext(msg)


def _LI(msg):
    return t.ugettext(msg)


def _LW(msg):
    return t.ugettext(msg)


def _LE(msg):
    return t.ugettext(msg)


def _LC(msg):
    return t.ugettext(msg)
