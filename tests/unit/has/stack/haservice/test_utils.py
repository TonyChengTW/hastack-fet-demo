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
Test suite for utils.
"""
from hastack.has.stack.haservice import constants as ha_constants
from hastack.has.stack.haservice import exception as service_exception
from hastack.has.stack.haservice import utils as ha_utils
from nova import test
from nova import utils as nova_utils


class Fake_Context(object):
    def __init__(self):
        self.is_admin = True

    def elevated(self):
        return self


class FakeHypervisorDriver(object):
    def __init__(self, flag):
        self.flag = flag

    def hypervisor_is_up(self, context, hv_name, **kwargs):
        return self.flag


class UtilsTestCase(test.TestCase):
    def setUp(self):
        super(UtilsTestCase, self).setUp()
        self.down_time = 3

    def test_get_image_from_inst(self):
        self.mox.StubOutWithMock(nova_utils, 'instance_sys_meta')
        self.mox.StubOutWithMock(nova_utils, 'get_image_from_system_metadata')

        nova_utils.instance_sys_meta('instance').AndReturn('system_meta')
        nova_utils.get_image_from_system_metadata(
            'system_meta').AndReturn('result')
        self.mox.ReplayAll()
        self.assertEqual(ha_utils.get_image_from_inst('instance'), 'result')

    def test_hypervisor_is_up(self):
        # hypervisor_is_up has error at policy_engine_manager
        pass

    def test_validate_policy_parameters(self):
        policy = {'haservice-id': 1}
        self.assertRaises(service_exception.HAServiceNotFound,
                         ha_utils.validate_policy_parameters,
                         policy, [2, 3])

        policy[ha_constants.KEY_ID] = 0
        self.assertRaises(service_exception.InvalidHAServiceInput,
                          ha_utils.validate_policy_parameters,
                          policy)
        policy[ha_constants.KEY_ID] = 1
        policy[ha_constants.KEY_RUN_INTERVAL] = 0
        self.assertRaises(service_exception.InvalidHAServiceInput,
                          ha_utils.validate_policy_parameters,
                          policy)
        policy[ha_constants.KEY_RUN_INTERVAL] = 1
        policy[ha_constants.KEY_STABILIZATION] = 0
        self.assertRaises(service_exception.InvalidHAServiceInput,
                          ha_utils.validate_policy_parameters,
                          policy)
        policy[ha_constants.KEY_STABILIZATION] = 1
        ha_utils.validate_policy_parameters(policy)

        policy[ha_constants.KEY_STATE] = 'not_enabled_or_disabled'
        self.assertRaises(service_exception.InvalidHAServiceState,
                          ha_utils.validate_policy_parameters,
                          policy)
        policy[ha_constants.KEY_STATE] = 'enabled'
        ha_utils.validate_policy_parameters(policy)

    def test_check_hv_status_json_keys(self):
        orig_stat = {
            'ha': {
                'host1': {
                    'state': 'state1',
                    'created_at': 'time1',
                    'updated_at': 'time1'
                }
            },
            'maintenance': {
                'host2': {
                    'state': 'state2',
                    'migrate': 'migrate',
                    'created_at': 'time2',
                    'updated_at': 'time2',
                    'target_host': 'host1'
                }
            }
        }
        copy_stat = orig_stat.copy()
        ha_utils.check_hv_status_json_keys(copy_stat)
        self.assertEqual(copy_stat, orig_stat)
        orig_stat['ha']['host1'].pop('state')
        orig_stat['maintenance']['host2'].pop('state')
        expected_stat = {'ha': {}, 'maintenance': {}}
        ha_utils.check_hv_status_json_keys(orig_stat)
        self.assertEqual(orig_stat, expected_stat)
