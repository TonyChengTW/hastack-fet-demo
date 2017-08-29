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
Test suite for ipmi_utils.
"""
import json
import mock
from oslo_config import cfg
from pyghmi.ipmi import command

from hastack.has.stack.haservice import ipmi_utils
from nova import objects
from nova import test


CONF = cfg.CONF

metrics = [
    {
        'name': 'bmc',
        'value': 'value1'
    },
    {
        'name': 'user',
        'value': 'value2'
    },
    {
        'name': 'password',
        'value': 'value3'
    }
]

node1 = objects.ComputeNode(id=1,
                hypervisor_hostname='compute1',
                hypervisor_type='QEMU',
                host='compute1',
                stats=None,
                metrics=None)

node1.metrics = json.dumps(metrics)


class IpmiUtilsTestCase(test.TestCase):
    def setUp(self):
        super(IpmiUtilsTestCase, self).setUp()

    def test_get_bmc(self):
        result = ipmi_utils.get_bmc(node1)
        self.assertEqual(result, ('value1', 'value2', 'value3'))

    @mock.patch.object(command, 'Command')
    @mock.patch.object(ipmi_utils, 'get_bmc')
    def test_get_power(self, mock_get_bmc, mock_command):
        mock_get_bmc.return_value = ('bmc', 'user', 'password')
        mock_ipmi = mock.Mock()
        mock_command.return_value = mock_ipmi
        mock_ipmi.get_power.return_value = {'powerstate': 'on'}
        result = ipmi_utils.get_power(node1)
        self.assertEqual(result, 'on')
        mock_get_bmc.assert_called_once_with(node1)
        mock_command.assert_called_once_with(bmc='bmc', userid='user',
                                             password='password')
        self.assertTrue(mock_ipmi.get_power.called)
