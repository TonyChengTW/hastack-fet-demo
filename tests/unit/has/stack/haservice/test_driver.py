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
Test suite for driver.py.
"""
import mock
from pyghmi.ipmi import command
import requests

from hastack.has.stack.haservice.fencing_driver import driver as fencing_driver
from hastack.has.stack.haservice.hypervisor_driver import driver as hv_driver
from hastack.has.stack.haservice.instance_driver import driver as inst_driver
from hastack.has.stack.haservice import utils
from nova import objects
from nova import servicegroup
from nova import test


COMPUTE_NODES = [
    objects.ComputeNode(id=1,
                hypervisor_hostname='compute1',
                hypervisor_type='QEMU',
                host='compute1'),
    objects.ComputeNode(id=2,
                hypervisor_hostname='compute2',
                hypervisor_type='QEMU',
                host='compute2'),
    objects.ComputeNode(id=3,
                hypervisor_hostname='compute2',
                hypervisor_type='VMware vCenter Server',
                host='compute2')
]

INSTANCES = [
    {
        'name': 'vm1',
        'vm_state': 'active',
        'launched_at': '1',
        'metadata': {'ha': 'True'}
    },
    {
        'name': 'vm2',
        'vm_state': 'stopped',
        'launched_at': '2',
        'metadata': {'ha': 'True'}
    },
]

HOST_STATE = '''
             [
                {
                    "ModifyIndex": 7,
                    "CreateIndex": 6,
                    "Node": "compute1",
                    "CheckID": "mng_ping",
                    "Name": "mng_ping",
                    "Status": "critical",
                    "Notes": "",
                    "Output": "",
                    "ServiceID": "",
                    "ServiceName": ""
                }
             ]
             '''


@classmethod
def fake_compute_node_get_all(cls, context):
    return COMPUTE_NODES


@classmethod
def fake_service_get_by_compute_host(cls, context, host):
    return {'is_up': True}


class Fake_ComputeNodeList(object):
    @classmethod
    def get_by_hypervisor(cls, context, hypervisor_match):
        return [COMPUTE_NODES[0]]

    @classmethod
    def get_all(cls, context):
        return COMPUTE_NODES


class Fake_InstanceList(object):
    @classmethod
    def get_by_host(cls, context, host, expected_attrs=None,
                    use_slave=False):
        return INSTANCES


class Fake_API(object):
    def service_is_up(self, service):
        return service['is_up']


class Fake_Context(object):
    def __init__(self):
        self.is_admin = True

    def elevated(self):
        return self


class HADriverTestCase(test.TestCase):
    def setUp(self):
        super(HADriverTestCase, self).setUp()

        def fake_hypervisor_is_up(context, hv_name):
            return False
        self.stubs.Set(utils, 'hypervisor_is_up',
                       fake_hypervisor_is_up)

    def test_can_enter_maintenance(self):
        hvs_driver = hv_driver.HAHypervisorDriver()
        fake_ctx = Fake_Context()
        result = hvs_driver.can_enter_maintenance(fake_ctx, "compute1", "all")
        self.assertTrue(result[0])

    @mock.patch.object(objects.InstanceList, 'get_by_host')
    def test_select_instances(self, mock_method):
        mock_method.return_value = INSTANCES
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)
        servicegroup.API = Fake_API
        objects.ComputeNodeList = Fake_ComputeNodeList
        instance_driver = inst_driver.HAInstanceDriver()
        ctx = Fake_Context()
        instances = instance_driver.select_instances(ctx, "compute1")
        self.assertEqual(2, len(instances))

    @mock.patch.object(requests, 'request')
    def test_get_host_status(self, mock_request):
        mock_request.return_value.text = HOST_STATE
        hvs_driver = hv_driver.HAHypervisorDriver()
        result = hvs_driver.get_host_status(COMPUTE_NODES[0])
        self.assertEqual(result, (False, False, False))
        self.assertEqual(mock_request.call_count, 3)

    def test_hypervisor_is_up(self):
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)
        servicegroup.API = Fake_API
        objects.ComputeNodeList = Fake_ComputeNodeList
        hvs_driver = hv_driver.HAHypervisorDriver()
        ctx = Fake_Context()
        self.assertEqual(True, hvs_driver.hypervisor_is_up(ctx, 'compute1'))
        self.assertEqual(False, hvs_driver.hypervisor_is_up(ctx, 'compute2'))

    def test_ipmi_fencing_host(self):
        mock_return = mock.Mock()
        mock_command = mock.Mock(return_value=mock_return)
        command.Command = mock_command
        fenc_driver = fencing_driver.IPMIFencingDriver()
        ctx = Fake_Context
        fenc_driver.fencing_host(ctx, 'bmc', 'user', 'password')
        mock_command.assert_called_once_with(bmc='bmc', userid='user',
                                            password='password')
        mock_return.set_power.assert_called_once_with('off')
