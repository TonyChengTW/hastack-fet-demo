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
Test suite for engine.
"""
import mock
from mox3 import mox
from oslo_config import cfg

from hastack.has.stack.haservice import constants
from hastack.has.stack.haservice import engine as engines
from hastack.has.stack.haservice.instance_driver \
import driver as instance_driver
from hastack.has.stack.haservice import ipmi_utils
from hastack.has.stack.haservice import utils as ha_utils
from hastack.has.stack import hv_status
from nova.db import api as db_api
from nova import objects
from nova.objects import instance as instance_obj
from nova.scheduler import utils as scheduler_utils
from nova import test
from nova.tests.unit import fake_instance


CONF = cfg.CONF

all_nodes = [
    {'host': 'host1',
     'hypervisor_hostname': 'host1.local'},
    {'host': 'host2',
     'hypervisor_hostname': 'host2.local'},
    {'host': 'host3',
     'hypervisor_hostname': 'host3.local'},
    {'host': 'host4',
     'hypervisor_hostname': 'host4.local'}
]

COMPUTE_NODES = [
    objects.ComputeNode(id=1,
                hypervisor_hostname='compute1',
                hypervisor_type='QEMU',
                host='compute1',
                stats=None,
                metrics=None),
    objects.ComputeNode(id=2,
                hypervisor_hostname='compute2',
                hypervisor_type='QEMU',
                host='compute2',
                stats=None,
                metrics=None),
]

INSTANCES = [
    {
        'uuid': 'uuid1',
        'name': 'vm1',
        'vm_state': 'active',
        'task_state': None,
        'instance_type_id': '1',
        'launched_at': '1'
    },
    {
        'uuid': 'uuid2',
        'name': 'vm2',
        'vm_state': 'stopped',
        'task_state': None,
        'instance_type_id': '1',
        'launched_at': '2'
    },
]

json = {
        'version': '2.0',
        'ha': {
            'host1.local': {
                 'state': constants.STATE_OK
            },
            'host2.local': {
                 'state': constants.STATE_HA_EVACUATED
            }
        }
}

status = hv_status.HypervisorStatus(json)


@classmethod
def fake_compute_node_get_all(cls, context):
    return COMPUTE_NODES


@classmethod
def fake_service_get_by_compute_host(cls, context, host):
    return 'service'


class Fake_InstanceList(object):
    @classmethod
    def get_by_host(cls, context, host, expected_attrs=None,
                    use_slave=False):
        return INSTANCES


class Fake_Context(object):
    def __init__(self):
        self.is_admin = True
        self.request_id = 'requestid'

    def elevated(self):
        return 'elevated'


class Fake_HASDriver(object):
    def get_context(self, ctxt=None, context_service_catalog=None):
        fake_context = Fake_Context()
        return fake_context


class BasePolicyEngineTestCase(test.TestCase):
    def setUp(self):
        super(BasePolicyEngineTestCase, self).setUp()
        self.stubs.Set(objects.ComputeNodeList, 'get_all',
                       fake_compute_node_get_all)
        self.engine = engines.BasePolicyEngine(host=all_nodes[0],
                                               has_driver=Fake_HASDriver())

    def test_reset(self):
        self.engine.reset()
        self.assertEqual(self.engine.idle_hvs, set())
        self.assertEqual(self.engine.violated_hvs, set())
        self.assertEqual(self.engine.in_action_hvs, set())
        self.assertEqual(self.engine.error_insts, {})


class HAEngineTestCase(test.TestCase):
    def setUp(self):
        super(HAEngineTestCase, self).setUp()
        self.stubs.Set(objects.ComputeNodeList, 'get_all',
                       fake_compute_node_get_all)
        self.engine = engines.HAEngine(host=all_nodes[0],
                                       has_driver=Fake_HASDriver())
        self.context = self.engine.ctxt
        self.hv_name = 'compute1'
        self.inst_list = [{'uuid': 'uuid1', 'vm_state': 'active',
                           'task_state': None}]
        self.instance_host = "compute1"
        self.instance_uuid = "uuid1"
        self.instance_image = "image"
        self.instance_vm_state = "active"
        self.instance_task_state = None
        self.instance_node = "compute1"
        db_instance = fake_instance.fake_db_instance(
                host=self.instance_host,
                uuid=self.instance_uuid,
                vm_state=self.instance_vm_state,
                task_state=self.instance_task_state,
                memory_mb=512,
                instance_type_id=1,
                node=self.instance_node,
                image_ref=self.instance_image)
        self.instance = objects.Instance._from_db_object(
                self.context, objects.Instance(), db_instance)

    def test_reset(self):
        self.engine.reset()
        self.assertEqual(self.engine.current_interval, 0)
        self.assertEqual(self.engine.violated_count, {})
        self.assertEqual(self.engine.idle_hvs, set())
        self.assertEqual(self.engine.violated_hvs, set())
        self.assertEqual(self.engine.in_action_hvs, set())
        self.assertEqual(self.engine.error_insts, {})

    def test_select_nodes(self):
        result = self.engine.select_nodes(self.engine.ctxt)
        self.assertEqual(result, COMPUTE_NODES)

    def test_check_host_network(self):
        mock_getstatus = mock.Mock()
        self.engine.host_driver.get_host_status = mock_getstatus
        mock_migrateinstance = mock.Mock()
        self.engine.migrate_instance = mock_migrateinstance
        mock_getstatus.return_value = (True, False, True)
        self.engine.check_host_network(None, COMPUTE_NODES[0])
        mock_getstatus.assert_called_once_with(COMPUTE_NODES[0])
        mock_migrateinstance.assert_called_once_with(None, COMPUTE_NODES[0])

    def test_check_host_power_status(self):
        self.mox.StubOutWithMock(ipmi_utils, 'get_power')
        self.mox.StubOutWithMock(self.engine, 'evacuate_instance')
        ipmi_utils.get_power(COMPUTE_NODES[0]).AndReturn('off')
        self.engine.evacuate_instance(None, COMPUTE_NODES[0])
        self.mox.ReplayAll()
        self.engine.check_host_power_status(None, COMPUTE_NODES[0])
        self.mox.VerifyAll()

    def test_update_managed_hvs(self):
        # def fake_aggregate_host_get_all(context, aggregate_id):
        #     return [all_nodes[0]['host']]
        #
        # self.stubs.Set(db, 'aggregate_host_get_all',
        #                fake_aggregate_host_get_all)
        # self.engine.update_managed_hvs(None, all_nodes)
        # self.assertEqual(self.engine.hv_map['host1.local'].host,
        #                  'host1')
        self.engine.update_managed_hvs(None, [COMPUTE_NODES[0]])
        self.assertEqual(self.engine.hv_map['compute1']['host'], 'compute1')
        self.assertFalse('compute2' in self.engine.violated_hvs)
        self.assertFalse('compute2' in self.engine.violated_count.keys())
        self.assertFalse('compute2' in self.engine.in_action_hvs)
        self.assertFalse('compute2' in self.engine.idle_hvs)

    def test_select_instance(self):
        with mock.patch.object(instance_driver.HAInstanceDriver,
                               'select_instances') as mock_method:
            mock_method.return_value = INSTANCES
            result = self.engine.select_instances(None, 'compute1')
            mock_method.assert_called_with(None, 'compute1')
            self.assertEqual(result, INSTANCES)

    def test_evacuate_instance(self):
        self.mox.StubOutWithMock(self.engine, 'select_instances')
        self.mox.StubOutWithMock(objects.InstanceList, 'get_by_filters')
        self.mox.StubOutWithMock(ha_utils, 'get_image_from_inst')
        self.mox.StubOutWithMock(scheduler_utils, 'build_request_spec')
        self.mox.StubOutWithMock(self.engine.scheduler_rpcapi,
                                 'select_destinations')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api, 'evacuate')

        self.engine.select_instances(self.context,
                    self.hv_name).AndReturn([(self.instance, None)])
        objects.InstanceList.get_by_filters(
            self.context, mox.IgnoreArg()).AndReturn([self.instance])
        ha_utils.get_image_from_inst(self.instance).AndReturn('image')
        scheduler_utils.build_request_spec(self.context, 'image',
                                           [self.instance]).AndReturn({})
        self.engine.scheduler_rpcapi.select_destinations(
            self.context, mox.IgnoreArg()).AndReturn(
            [{'host': 'compute2', 'nodename': 'compute2'}])
        objects.InstanceList.get_by_filters(
            self.context, mox.IgnoreArg()).AndReturn([self.instance])
        objects.Instance.get_by_uuid(mox.IgnoreArg(), mox.IgnoreArg(),
                    expected_attrs=mox.IgnoreArg()).AndReturn('instance')
        self.engine.compute_api.evacuate(mox.IgnoreArg(),
                                         'instance', 'compute2', True)
        self.mox.ReplayAll()
        self.engine.evacuate_instance(self.context, COMPUTE_NODES[0])

    def test_fencing_and_evacuate(self):
        self.mox.StubOutWithMock(ipmi_utils, 'get_bmc')
        self.mox.StubOutWithMock(ipmi_utils, 'get_power')
        self.mox.StubOutWithMock(self.engine.fencing_driver, 'fencing_host')
        self.mox.StubOutWithMock(self.engine.host_driver, 'hypervisor_is_up')
        self.mox.StubOutWithMock(self.engine, '_rebuild_instances')

        ipmi_utils.get_bmc(COMPUTE_NODES[0]).AndReturn(('bmc',
                                                        'user',
                                                        'password'))
        ipmi_utils.get_power(COMPUTE_NODES[0]).AndReturn('status')
        self.engine.fencing_driver.fencing_host(self.engine.ctxt,
                                                'bmc', 'user', 'password')
        self.engine.host_driver.hypervisor_is_up(self.engine.ctxt,
                                                 'compute1').AndReturn(False)
        self.engine._rebuild_instances(self.engine.ctxt, COMPUTE_NODES[0])
        self.mox.ReplayAll()
        result = self.engine.fencing_and_evacuate(self.engine.ctxt,
                                                  COMPUTE_NODES[0])
        self.assertEqual(result, True)

    @test.testtools.skip('This case is uncertainty.')
    def test_get_hv_moving_inst_map(self):
        mock_method = mock.Mock()
        self.engine.get_moving_insts = mock_method
        mock_method.side_effect = [{'uuid1': 'inst1'}, {'uuid2': 'inst2'}]
        hv_moving_inst_map = self.engine.get_hv_moving_inst_map()
        self.assertEqual(hv_moving_inst_map,
                         {'compute1': ['uuid1'], 'compute2': ['uuid2']})

    def test_live_migrate_instance(self):
        payload = {
            'hypervisor_hostname': 'compute1',
            'hypervisor_id': 1,
            'status': "TBD",
            'policy_type': 'haservice',
            'vm_name': None,
            'vm_uuid': 'uuid1',
            'action_name': 'live-migration',
            'target_host': 'compute2'
        }
        self.mox.StubOutWithMock(self.engine, 'select_instances')
        self.mox.StubOutWithMock(objects.InstanceList, 'get_by_filters')
        self.mox.StubOutWithMock(ha_utils, 'get_image_from_inst')
        self.mox.StubOutWithMock(scheduler_utils, 'build_request_spec')
        self.mox.StubOutWithMock(self.engine.scheduler_rpcapi,
                                 'select_destinations')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api, 'live_migrate')
        self.mox.StubOutWithMock(self.engine.notifier, 'info')

        self.engine.select_instances(self.context,
                    self.hv_name).AndReturn([(self.instance, None)])
        objects.InstanceList.get_by_filters(
                    self.context, mox.IgnoreArg()).AndReturn([self.instance])
        ha_utils.get_image_from_inst(self.instance).AndReturn('image')
        scheduler_utils.build_request_spec(self.context, 'image',
                                           [self.instance]).AndReturn({})
        self.engine.scheduler_rpcapi.select_destinations(
                self.context, mox.IgnoreArg()).AndReturn(
                [{'host': 'compute2', 'nodename': 'compute2'}])
        objects.Instance.get_by_uuid(mox.IgnoreArg(), mox.IgnoreArg(),
                expected_attrs=mox.IgnoreArg()).AndReturn(self.instance)
        self.engine.compute_api.live_migrate(mox.IgnoreArg(),
                                self.instance, False, False, 'compute2')
        self.engine.notifier.info(self.context,
                                  constants.ETYPE_HA_ACTION_START,
                                  mox.IgnoreArg())
        self.mox.ReplayAll()
        self.engine.migrate_instance(self.context, COMPUTE_NODES[0])
        self.assertEqual(self.engine.haservice_action['requestid'], payload)

    def test_cold_migrate_instance(self):
        payload = {
            'hypervisor_hostname': 'compute1',
            'hypervisor_id': 1,
            'status': "TBD",
            'policy_type': 'haservice',
            'vm_name': None,
            'vm_uuid': 'uuid1',
            'action_name': 'cold-migration',
            'target_host': 'compute2'
        }
        self.mox.StubOutWithMock(self.engine, 'select_instances')
        self.mox.StubOutWithMock(objects.InstanceList, 'get_by_filters')
        self.mox.StubOutWithMock(ha_utils, 'get_image_from_inst')
        self.mox.StubOutWithMock(objects.Flavor, 'get_by_id')
        self.mox.StubOutWithMock(scheduler_utils, 'build_request_spec')
        self.mox.StubOutWithMock(self.engine.scheduler_rpcapi,
                                 'select_destinations')
        self.mox.StubOutWithMock(scheduler_utils, 'populate_filter_properties')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(objects.Instance, 'save')
        self.mox.StubOutWithMock(objects.InstanceAction, 'action_start')
        self.mox.StubOutWithMock(self.engine.compute_rpcapi, 'prep_resize')
        self.mox.StubOutWithMock(self.engine.notifier, 'info')

        self.instance['vm_state'] = 'stopped'
        self.engine.select_instances(self.context,
                self.hv_name).AndReturn([(self.instance, None)])
        objects.InstanceList.get_by_filters(
                self.context, mox.IgnoreArg()).AndReturn([self.instance])
        ha_utils.get_image_from_inst(self.instance).AndReturn('image')
        objects.Flavor.get_by_id(self.context,
                self.instance['instance_type_id']).AndReturn('flavor')
        scheduler_utils.build_request_spec(self.context, 'image',
                [self.instance], instance_type='flavor').AndReturn(
                {'instance_type': {'extra_specs': {}}})
        self.engine.scheduler_rpcapi.select_destinations(
                self.context, mox.IgnoreArg()).AndReturn(
                        [{'host': 'compute2', 'nodename': 'compute2'}])
        scheduler_utils.populate_filter_properties(mox.IgnoreArg(),
                                                   mox.IgnoreArg())
        objects.Instance.get_by_uuid(mox.IgnoreArg(), mox.IgnoreArg(),
                expected_attrs=mox.IgnoreArg()).AndReturn(self.instance)
        objects.Instance.save(expected_task_state=[None])
        objects.InstanceAction.action_start(self.context, 'uuid1',
                                            'resize', want_result=False)
        self.engine.compute_rpcapi.prep_resize(mox.IgnoreArg(), 'image',
                                    self.instance, 'flavor', 'compute2', None,
                                    request_spec=mox.IgnoreArg(),
                                    filter_properties=mox.IgnoreArg(),
                                    node='compute2')
        self.engine.notifier.info(self.context,
                                  constants.ETYPE_HA_ACTION_START,
                                  mox.IgnoreArg())
        self.mox.ReplayAll()
        self.engine.migrate_instance(self.context, COMPUTE_NODES[0])
        self.assertEqual(self.engine.haservice_action['has-ha-requestid'],
                         payload)

    def test_live_migration_inst_fail(self):
        payload = {'instance_id': 'uuid1', 'hostname': 'compute1'}
        self.engine.error_insts = {'compute1': {'uuid1': 2}}
        self.engine.haservice_action = {
            'requestid': {'hypervisor_hostname': 'compute1'}
        }
        action_info = {'hypervisor_hostname': 'compute1',
                      'action_result': 'failed'}

        self.mox.StubOutWithMock(self.engine, 'get_moving_insts')
        self.mox.StubOutWithMock(self.engine.notifier, 'info')

        self.engine.get_moving_insts('compute1').AndReturn(
                    {'uuid1': 'compute2'})
        self.engine.notifier.info(self.context,
                                  'has.ha.ha_moving.fail',
                                  mox.IgnoreArg())
        self.engine.notifier.info(self.context,
                                  constants.ETYPE_HA_ACTION_END,
                                  action_info)
        self.mox.ReplayAll()
        self.engine.move_inst_fail(self.context, 'compute1', payload, True)
        self.assertFalse('compute1' in self.engine.idle_hvs)
        self.assertTrue('compute1' in self.engine.in_action_hvs)
        self.assertEqual(self.engine.error_insts['compute1']['uuid1'], 3)

    def test_cold_migration_inst_fail(self):
        payload = {'instance_id': 'uuid1', 'hostname': 'compute1'}
        self.engine.error_insts = {'compute1': {'uuid1': 2}}
        self.engine.haservice_action = {
            'requestid': {'hypervisor_hostname': 'compute1'}
        }
        action_info = {'hypervisor_hostname': 'compute1',
                      'action_result': 'failed'}

        self.mox.StubOutWithMock(self.engine, 'get_moving_insts')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.notifier, 'info')

        self.engine.get_moving_insts('compute1').AndReturn(
                    {'uuid1': 'compute2'})
        objects.Instance.get_by_uuid(self.context, 'uuid1',
                    expected_attrs=[]).AndReturn(self.instance)
        self.engine.notifier.info(self.context,
                                  'has.ha.ha_moving.fail',
                                  mox.IgnoreArg())
        self.engine.notifier.info(self.context,
                                  constants.ETYPE_HA_ACTION_END,
                                  action_info)

        self.mox.ReplayAll()
        self.engine.move_inst_fail(self.context, 'compute1', payload, False)
        self.assertEqual(self.engine.error_insts['compute1']['uuid1'], 4)

    def test_move_inst_success(self):
        self.engine.haservice_action = {
            'requestid': {'hypervisor_hostname': 'compute1'}
        }
        payload = {'hypervisor_hostname': 'compute1',
                   'action_result': 'success'}
        self.mox.StubOutWithMock(self.engine.notifier, 'info')

        self.engine.notifier.info(self.context, 'has.ha.ha_action.end',
                                  payload)
        self.mox.ReplayAll()
        self.engine.move_inst_success(self.context)

    def test_service_function_disable_haservice(self):
        db_migration = {
            'id': 1,
            'source_compute': 'compute1',
            'dest_compute': 'compute2',
            'source_node': 'compute1',
            'dest_node': 'compute2',
            'dest_host': 'compute2',
            'old_instance_type_id': 123,
            'new_instance_type_id': 123,
            'instance_uuid': 'uuid1',
            'status': 'finished',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False,
            'migration_type': 'migration',
            'hidden': False,
            'memory_total': 123,
            'memory_processed': 23,
            'memory_remaining': 100,
            'disk_total': 123,
            'disk_processed': 23,
            'disk_remaining': 100
        }
        db_action = {
            'id': 1,
            'action': 'action',
            'instance_uuid': 'uuid1',
            'request_id': 'has-ha-requestid',
            'user_id': 'user1',
            'project_id': 'project1',
            'start_time': None,
            'finish_time': None,
            'message': 'msg',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        db_haservice = {
            'id': 1,
            'host': 'host',
            'binary': 'hastack.haservice',
            'topic': 'haservice',
            'report_count': 123,
            'disabled': False,
            'disabled_reason': None,
            'availability_zone': None,
            'compute_node': None,
            'last_seen_up': None,
            'forced_down': False,
            'version': 123,
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        migration = objects.Migration._from_db_object(
            self.context, objects.Migration(), db_migration
        )
        action = objects.InstanceAction._from_db_object(
            self.context, objects.InstanceAction(), db_action
        )
        haservice = objects.Service._from_db_object(
            self.context, objects.Service(), db_haservice
        )
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)

        self.mox.StubOutWithMock(objects.MigrationList, 'get_by_filters')
        self.mox.StubOutWithMock(objects.InstanceActionList,
                                 'get_by_instance_uuid')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api,
                                 'confirm_resize')
        self.mox.StubOutWithMock(self.engine.servicegroup_api,
                                 'service_is_up')
        self.mox.StubOutWithMock(db_api, 'service_get_by_host_and_binary')
        self.mox.StubOutWithMock(db_api, 'service_update')
        self.mox.StubOutWithMock(self.engine, 'select_nodes')
        self.mox.StubOutWithMock(self.engine, 'check_host_power_status')
        self.mox.StubOutWithMock(self.engine, 'check_vm_status')
        objects.MigrationList.get_by_filters(
            self.context, {'status': 'finished'}).AndReturn([migration])
        objects.InstanceActionList.get_by_instance_uuid(
            self.context, migration['instance_uuid']
        ).AndReturn([action])
        objects.Instance.get_by_uuid(
            self.context, migration['instance_uuid'],
            expected_attrs=instance_obj.INSTANCE_DEFAULT_FIELDS).AndReturn(
            self.instance
        )
        self.engine.compute_api.confirm_resize(self.context, self.instance)
        self.engine.select_nodes(self.context).AndReturn(COMPUTE_NODES)
        db_api.service_get_by_host_and_binary(self.context, self.engine.host,
                                    'hastack.haservice').AndReturn(haservice)
        for i in range(0, len(COMPUTE_NODES)):
            self.engine.servicegroup_api.service_is_up(
                'service').AndReturn(False)
        db_api.service_update(self.context, int(haservice['id']),
                              {'disabled': True})
        self.mox.ReplayAll()
        self.engine.service_function(self.context)

    def test_service_function_not_disable_haservice(self):
        db_migration = {
            'id': 1,
            'source_compute': 'compute1',
            'dest_compute': 'compute2',
            'source_node': 'compute1',
            'dest_node': 'compute2',
            'dest_host': 'compute2',
            'old_instance_type_id': 123,
            'new_instance_type_id': 123,
            'instance_uuid': 'uuid1',
            'status': 'finished',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False,
            'migration_type': 'migration',
            'hidden': False,
            'memory_total': 123,
            'memory_processed': 23,
            'memory_remaining': 100,
            'disk_total': 123,
            'disk_processed': 23,
            'disk_remaining': 100
        }
        db_action = {
            'id': 1,
            'action': 'action',
            'instance_uuid': 'uuid1',
            'request_id': 'has-ha-requestid',
            'user_id': 'user1',
            'project_id': 'project1',
            'start_time': None,
            'finish_time': None,
            'message': 'msg',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        db_haservice = {
            'id': 1,
            'host': 'host',
            'binary': 'hastack.haservice',
            'topic': 'haservice',
            'report_count': 123,
            'disabled': False,
            'disabled_reason': None,
            'availability_zone': None,
            'compute_node': None,
            'last_seen_up': None,
            'forced_down': False,
            'version': 123,
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        migration = objects.Migration._from_db_object(
            self.context, objects.Migration(), db_migration
        )
        action = objects.InstanceAction._from_db_object(
            self.context, objects.InstanceAction(), db_action
        )
        haservice = objects.Service._from_db_object(
            self.context, objects.Service(), db_haservice
        )
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)

        self.mox.StubOutWithMock(objects.MigrationList, 'get_by_filters')
        self.mox.StubOutWithMock(objects.InstanceActionList,
                                 'get_by_instance_uuid')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api,
                                 'confirm_resize')
        self.mox.StubOutWithMock(self.engine.servicegroup_api,
                                 'service_is_up')
        self.mox.StubOutWithMock(self.engine, 'select_nodes')
        self.mox.StubOutWithMock(db_api, 'service_get_by_host_and_binary')
        self.mox.StubOutWithMock(self.engine, 'check_host_power_status')
        self.mox.StubOutWithMock(self.engine, 'check_vm_status')

        objects.MigrationList.get_by_filters(
            self.context, {'status': 'finished'}).AndReturn([migration])
        objects.InstanceActionList.get_by_instance_uuid(
            self.context, migration['instance_uuid']
        ).AndReturn([action])
        objects.Instance.get_by_uuid(
            self.context, migration['instance_uuid'],
            expected_attrs=instance_obj.INSTANCE_DEFAULT_FIELDS).AndReturn(
            self.instance
        )
        self.engine.compute_api.confirm_resize(self.context, self.instance)
        self.engine.select_nodes(self.context).AndReturn(COMPUTE_NODES)
        db_api.service_get_by_host_and_binary(self.context, self.engine.host,
                                    'hastack.haservice').AndReturn(haservice)
        for i in range(0, len(COMPUTE_NODES)):
            self.engine.servicegroup_api.service_is_up(
                'service').AndReturn(True)
        for node in COMPUTE_NODES:
            self.engine.check_host_power_status(self.context, node)
            self.engine.check_vm_status(self.context, node)
        self.mox.ReplayAll()
        self.engine.service_function(self.context)

    def test_service_function_enable_haservice(self):
        db_migration = {
            'id': 1,
            'source_compute': 'compute1',
            'dest_compute': 'compute2',
            'source_node': 'compute1',
            'dest_node': 'compute2',
            'dest_host': 'compute2',
            'old_instance_type_id': 123,
            'new_instance_type_id': 123,
            'instance_uuid': 'uuid1',
            'status': 'finished',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False,
            'migration_type': 'migration',
            'hidden': False,
            'memory_total': 123,
            'memory_processed': 23,
            'memory_remaining': 100,
            'disk_total': 123,
            'disk_processed': 23,
            'disk_remaining': 100
        }
        db_action = {
            'id': 1,
            'action': 'action',
            'instance_uuid': 'uuid1',
            'request_id': 'has-ha-requestid',
            'user_id': 'user1',
            'project_id': 'project1',
            'start_time': None,
            'finish_time': None,
            'message': 'msg',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        db_haservice = {
            'id': 1,
            'host': 'host',
            'binary': 'hastack.haservice',
            'topic': 'haservice',
            'report_count': 123,
            'disabled': True,
            'disabled_reason': None,
            'availability_zone': None,
            'compute_node': None,
            'last_seen_up': None,
            'forced_down': False,
            'version': 123,
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        migration = objects.Migration._from_db_object(
            self.context, objects.Migration(), db_migration
        )
        action = objects.InstanceAction._from_db_object(
            self.context, objects.InstanceAction(), db_action
        )
        haservice = objects.Service._from_db_object(
            self.context, objects.Service(), db_haservice
        )
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)

        self.mox.StubOutWithMock(objects.MigrationList, 'get_by_filters')
        self.mox.StubOutWithMock(objects.InstanceActionList,
                                 'get_by_instance_uuid')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api,
                                 'confirm_resize')
        self.mox.StubOutWithMock(self.engine.servicegroup_api,
                                 'service_is_up')
        self.mox.StubOutWithMock(db_api, 'service_get_by_host_and_binary')
        self.mox.StubOutWithMock(db_api, 'service_update')
        self.mox.StubOutWithMock(self.engine, 'select_nodes')
        self.mox.StubOutWithMock(self.engine, 'check_host_power_status')
        self.mox.StubOutWithMock(self.engine, 'check_vm_status')

        objects.MigrationList.get_by_filters(
            self.context, {'status': 'finished'}).AndReturn([migration])
        objects.InstanceActionList.get_by_instance_uuid(
            self.context, migration['instance_uuid']
        ).AndReturn([action])
        objects.Instance.get_by_uuid(
            self.context, migration['instance_uuid'],
            expected_attrs=instance_obj.INSTANCE_DEFAULT_FIELDS).AndReturn(
            self.instance
        )
        self.engine.compute_api.confirm_resize(self.context, self.instance)
        self.engine.select_nodes(self.context).AndReturn(COMPUTE_NODES)
        db_api.service_get_by_host_and_binary(self.context, self.engine.host,
                                    'hastack.haservice').AndReturn(haservice)
        for i in range(0, len(COMPUTE_NODES)):
            self.engine.servicegroup_api.service_is_up(
                'service').AndReturn(True)
        db_api.service_update(self.context, int(haservice['id']),
                              {'disabled': False})
        self.mox.ReplayAll()
        self.engine.service_function(self.context)

    def test_service_function_not_enable_haservice(self):
        db_migration = {
            'id': 1,
            'source_compute': 'compute1',
            'dest_compute': 'compute2',
            'source_node': 'compute1',
            'dest_node': 'compute2',
            'dest_host': 'compute2',
            'old_instance_type_id': 123,
            'new_instance_type_id': 123,
            'instance_uuid': 'uuid1',
            'status': 'finished',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False,
            'migration_type': 'migration',
            'hidden': False,
            'memory_total': 123,
            'memory_processed': 23,
            'memory_remaining': 100,
            'disk_total': 123,
            'disk_processed': 23,
            'disk_remaining': 100
        }
        db_action = {
            'id': 1,
            'action': 'action',
            'instance_uuid': 'uuid1',
            'request_id': 'has-ha-requestid',
            'user_id': 'user1',
            'project_id': 'project1',
            'start_time': None,
            'finish_time': None,
            'message': 'msg',
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        db_haservice = {
            'id': 1,
            'host': 'host',
            'binary': 'hastack.haservice',
            'topic': 'haservice',
            'report_count': 123,
            'disabled': True,
            'disabled_reason': None,
            'availability_zone': None,
            'compute_node': None,
            'last_seen_up': None,
            'forced_down': False,
            'version': 123,
            'created_at': None,
            'updated_at': None,
            'deleted_at': None,
            'deleted': False
        }
        migration = objects.Migration._from_db_object(
            self.context, objects.Migration(), db_migration
        )
        action = objects.InstanceAction._from_db_object(
            self.context, objects.InstanceAction(), db_action
        )
        haservice = objects.Service._from_db_object(
            self.context, objects.Service(), db_haservice
        )
        self.stubs.Set(objects.Service, 'get_by_compute_host',
                       fake_service_get_by_compute_host)

        self.mox.StubOutWithMock(objects.MigrationList, 'get_by_filters')
        self.mox.StubOutWithMock(objects.InstanceActionList,
                                 'get_by_instance_uuid')
        self.mox.StubOutWithMock(objects.Instance, 'get_by_uuid')
        self.mox.StubOutWithMock(self.engine.compute_api,
                                 'confirm_resize')
        self.mox.StubOutWithMock(self.engine.servicegroup_api,
                                 'service_is_up')
        self.mox.StubOutWithMock(db_api, 'service_get_by_host_and_binary')
        self.mox.StubOutWithMock(self.engine, 'select_nodes')
        self.mox.StubOutWithMock(self.engine, 'check_host_power_status')
        self.mox.StubOutWithMock(self.engine, 'check_vm_status')

        objects.MigrationList.get_by_filters(
            self.context, {'status': 'finished'}).AndReturn([migration])
        objects.InstanceActionList.get_by_instance_uuid(
            self.context, migration['instance_uuid']
        ).AndReturn([action])
        objects.Instance.get_by_uuid(
            self.context, migration['instance_uuid'],
            expected_attrs=instance_obj.INSTANCE_DEFAULT_FIELDS).AndReturn(
            self.instance
        )
        self.engine.compute_api.confirm_resize(self.context, self.instance)
        self.engine.select_nodes(self.context).AndReturn(COMPUTE_NODES)
        db_api.service_get_by_host_and_binary(self.context, self.engine.host,
                                    'hastack.haservice').AndReturn(haservice)
        self.engine.servicegroup_api.service_is_up(
                'service').AndReturn(False)
        self.mox.ReplayAll()
        self.engine.service_function(self.context)
