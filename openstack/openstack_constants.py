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
from nova.compute import instance_actions
from nova.compute import task_states
from nova.compute import vm_states
from nova.objects import instance as instance_obj

from nova.exception import NovaException
from nova.i18n import _

ACTIVE = vm_states.ACTIVE
STOPPED = vm_states.STOPPED
ERROR = vm_states.ERROR
PAUSED = vm_states.PAUSED


MIGRATING = task_states.MIGRATING
RESIZE_MIGRATING = task_states.RESIZE_MIGRATING
REBUILDING = task_states.REBUILDING
REBUILD_SPAWNING = task_states.REBUILD_SPAWNING
REBUILD_BLOCK_DEVICE_MAPPING = task_states.REBUILD_BLOCK_DEVICE_MAPPING
RESIZE_PREP = task_states.RESIZE_PREP


RESIZE = instance_actions.RESIZE


INSTANCE_DEFAULT_FIELDS = instance_obj.INSTANCE_DEFAULT_FIELDS


class NoValidHost(NovaException):
    msg_fmt = _("No valid host was found. %(reason)s")


class NotFound(NovaException):
    msg_fmt = _("Resource could not be found.")
    code = 404


class InstanceNotFound(NotFound):
    ec2_code = 'InvalidInstanceID.NotFound'
    msg_fmt = _("Instance %(instance_id)s could not be found.")
