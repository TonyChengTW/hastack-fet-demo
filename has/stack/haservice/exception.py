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

from hastack.has.stack import has_gettextutils
from nova import exception

_ = has_gettextutils._


class HAServiceNotFound(exception.NotFound):
    msg_fmt = _("The policy engine manager could not find HA policy "
                "%(policy_id)r. Specify another HA policy.")


class InvalidHAServiceAction(exception.Invalid):
    msg_fmt = _("The policy engine manager cannot %(action)r on HA "
                "policy %(policy_id)r. Reason: %(reason)s")


class HAServiceConfFileNotFoundPath(exception.NotFound):
    msg_fmt = _("The policy engine manager could not find the HA "
                "policy configuration file: %(policy_conf)s")


class InvalidHAServiceState(exception.Invalid):
    msg_fmt = _("HA policy state should be 'disabled' or 'enabled'.")


class InvalidHAServiceInput(exception.Invalid):
    msg_fmt = _("The value %(value)r for %(attribute)r "
                "is invalid. Specify a number between "
                "%(min)d and %(max)d as the value.")


class HostMaintenanceError(exception.Invalid):
    msg_fmt = _("%(reason)s")
