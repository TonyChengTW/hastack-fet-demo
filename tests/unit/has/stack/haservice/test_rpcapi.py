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
Test suite for rpcapi.
"""
import contextlib
import mock
from oslo_config import cfg

from hastack.has.stack.haservice import rpcapi
from nova import context
from nova import test


CONF = cfg.CONF


class HAPolicyAPITestCase(test.TestCase):
    def setUp(self):
        super(HAPolicyAPITestCase, self).setUp()

    def _test_hapolicy_api(self, method, rpc_method, **kwargs):
        ctxt = context.RequestContext('fake_user', 'fake_project')
        hapolicyapi = rpcapi.HAPolicyAPI()
        self.assertIsNotNone(hapolicyapi.client)
        self.assertEqual(hapolicyapi.client.target.topic, CONF.haservice_topic)
        with contextlib.nested(
            mock.patch.object(hapolicyapi.client, rpc_method),
            mock.patch.object(hapolicyapi.client, 'prepare')
        ) as (
                rpc_mock, prepare_mock
        ):
            prepare_mock.return_value = hapolicyapi.client
            if rpc_method == 'call':
                rpc_mock.return_value = 'foo'
            else:
                rpc_mock.return_value = None
            retval = getattr(hapolicyapi, method)(ctxt, **kwargs)
            self.assertEqual(retval, rpc_mock.return_value)
            self.assertEqual(prepare_mock.call_count, 1)
            rpc_mock.assert_called_once_with(ctxt, method, **kwargs)

    def test_get_all(self):
        self._test_hapolicy_api('get_all', 'call')

    def test_get(self):
        self._test_hapolicy_api('get', 'call', policy_id='policy_id')

    def test_update(self):
        self._test_hapolicy_api('update', 'call', policy_id='policy_id',
                                updates='updates')

    def test_set_maintenance(self):
        self._test_hapolicy_api('set_maintenance', 'call',
                                hv_name='hv_name',
                                status='status', migrate='migrate',
                                target_host='target_host')

    def test_get_hv_status(self):
        self._test_hapolicy_api('get_hv_status', 'call')

    def test_hypervisor_list(self):
        self._test_hapolicy_api('hypervisor_list', 'call',
                                search_opts='search_opts')

    def test_event_list(self):
        self._test_hapolicy_api('event_list', 'call',
                                search_opts='search_opts',
                                marker='marker', limit='limit')
