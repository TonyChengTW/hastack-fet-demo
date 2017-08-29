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
Test suite for host status
"""

from hastack.has.stack.haservice import constants
from hastack.has.stack import hv_status
from nova import test


class HypervisorStatusTestCase(test.TestCase):
    def setUp(self):
        super(HypervisorStatusTestCase, self).setUp()
        json = {
            'version': '2.0',
            'ha': {
                'hostname1': {
                    'state': constants.STATE_OK,
                    'moving_insts': {}
                },
                'hostname2': {
                    'state': constants.STATE_HA_EVACUATED
                }
            }
        }
        self.hv_status = hv_status.HypervisorStatus(json)

    def test_get_ha(self):
        self.assertEqual(self.hv_status.get_ha('hostname1'),
                         constants.STATE_OK)

    def test_get_ha_moving_insts(self):
        self.assertEqual(self.hv_status.get_ha_moving_insts('hostname1'), {})

    def test_get_ha_moving_inst_start(self):
        self.hv_status.set_ha_moving_inst_start('hostname1',
                                                'inst1', '20140716')
        start = self.hv_status.get_ha_moving_inst_start('hostname1', 'inst1')
        self.assertEqual(start, '20140716')

    def test_get_ha_failed_instances(self):
        self.hv_status.ha_hvs.update({'hostname1': {}})
        self.hv_status.set_ha_failed_instances('hostname1',
                                               ['uuid1', 'uuid2'])
        failed_insts = self.hv_status.get_ha_failed_instances('hostname1')
        self.assertEqual(failed_insts, ['uuid1', 'uuid2'])

    def test_set_ha_failed_instances(self):
        self.hv_status.set_ha_failed_instances('hostname1',
                                               ['uuid1', 'uuid2'])
        self.assertEqual(
            self.hv_status.ha_hvs['hostname1']['failed_instances'],
            ['uuid1', 'uuid2'])

    def test_set_ha(self):
        self.hv_status.set_ha('hostname1', constants.STATE_HA_STARTED)
        self.assertEqual(self.hv_status.get_ha('hostname1'),
                         constants.STATE_HA_STARTED)

    def test_set_ha_moving_insts(self):
        self.hv_status.set_ha_moving_insts('hostname2', {})
        self.assertEqual(self.hv_status.get_ha_moving_insts('hostname2'), {})

    def test_set_ha_moving_inst_start(self):
        self.hv_status.set_ha_moving_inst_start('hostname1',
                                                'inst2', '20140716')
        start = self.hv_status.get_ha_moving_inst_start('hostname1', 'inst2')
        self.assertEqual(start, '20140716')

    def test_get_timestamp(self):
        result = self.hv_status.get_ha_timestamp('hostname3')
        self.assertEqual(result, {'created_at': '-', 'updated_at': '-'})

    def test_refresh(self):
        managed_hosts = set(['hostname1'])
        self.hv_status.refresh(managed_hosts)
        self.assertFalse('hostname2' in self.hv_status.ha_hvs)
