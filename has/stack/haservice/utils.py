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

"""Utilities for the HA policy service."""

from hastack.has.stack import constants
from hastack.has.stack import has_gettextutils
from hastack.has.stack.haservice import constants as ha_constants
from hastack.has.stack.haservice import exception as service_exception

import hastack.openstack.openstack_utils as openstack_utils

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

_ = has_gettextutils._
_LW = has_gettextutils._LW
_hv_drvr = None

LOG = logging.getLogger(__name__)


def get_image_from_inst(instance):
    # Get the system metadata from the instance
    system_meta = openstack_utils.instance_sys_meta(instance)

    # Convert the system metadata to image metadata
    return openstack_utils.get_image_from_system_metadata(system_meta)


def hypervisor_is_up(context, hv_name, **kwargs):
    """Check whether the hypervisor is up."""

    global _hv_drvr
    # we do this here to avoid circular imports
    if _hv_drvr is None:
        CONF = cfg.CONF
        CONF.import_opt('ha_policy_hypervisor_driver',
                        'hastack.has.stack.haservice.policy_engine_manager')
        _hv_drvr = importutils.import_object(CONF.ha_policy_hypervisor_driver)
    return _hv_drvr.hypervisor_is_up(context, hv_name, **kwargs)


def validate_policy_parameters(policy, id_list=None):
    def _check_parameter(policy, key1, key2):
        key = None
        if key1 in policy:
            key = key1
        elif key2 in policy:
            key = key2
        else:
            return

        try:
            if (int(policy[key]) < constants.MIN_POSITIVE_INT or
                    int(policy[key]) > constants.MAX_INT_32):
                raise Exception()
        except Exception:
            raise service_exception.InvalidHAServiceInput(
                                    value=policy[key],
                                    attribute=key,
                                    min=constants.MIN_POSITIVE_INT,
                                    max=constants.MAX_INT_32)

    # Check if id is valid in metadata
    if id_list:
        if (("haservice-id" in policy) and
               (policy["haservice-id"] not in id_list)):
            raise service_exception.HAServiceNotFound(
                    policy_id=policy["haservice-id"])

    _check_parameter(policy, ha_constants.KEY_ID, ha_constants.KEY_HA_ID)
    _check_parameter(policy, ha_constants.KEY_RUN_INTERVAL,
                     ha_constants.KEY_HA_RUN_INTERVAL)
    _check_parameter(policy, ha_constants.KEY_STABILIZATION,
                     ha_constants.KEY_HA_STABILIZATION)

    # Test state if exists
    key_state = ha_constants.KEY_STATE
    if key_state in policy:
        if (policy[key_state] not in [ha_constants.ENABLED,
                                      ha_constants.DISABLED]):
            raise service_exception.InvalidHAServiceState()


def check_hv_status_json_keys(json_stat):
    ha_fixed_key = ['state', 'created_at', 'updated_at']
    mt_fixed_key = ['state', 'migrate', 'created_at', 'updated_at',
                    'target_host']

    def check_keys(json_status, func_item, check_item):
        hv_names = json_status[func_item].keys()
        for hv_name in hv_names:
            diff_item = (set(check_item) -
                set(json_status[func_item][hv_name].keys()))
            if len(diff_item) != 0:
                for diff_keys in diff_item:
                    LOG.warning(_LW('The %(f_item)s state key for hypervisor '
                               '%(hyper_name)s is missing the key %(st_key)s.')
                             % {'f_item': func_item,
                                'hyper_name': hv_name,
                                'st_key': diff_keys})
                json_status[func_item].pop(hv_name)
                LOG.warning(_LW('The %(f_item)s state key for hypervisor '
                           '%(hyper_name)s was deleted because it was '
                           'unexpectedly corrupted and this deletion '
                           'will remedy the situation.')
                         % {'f_item': func_item, 'hyper_name': hv_name})
    check_keys(json_stat, 'ha', ha_fixed_key)
    check_keys(json_stat, 'maintenance', mt_fixed_key)
