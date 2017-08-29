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

"""Base engine for HA and maintenance."""

import ast
import eventlet

import hastack.has.conf as ha_conf
from hastack.has.stack import constants
from hastack.has.stack import has_gettextutils
from hastack.has.stack.haservice import constants as ha_constants
from hastack.has.stack.haservice import ipmi_utils
from hastack.has.stack.haservice import utils as ha_utils
from hastack.has.stack import utils
from hastack.openstack.openstack_api.api import ComputeAPI
from hastack.openstack.openstack_api.api import ComputeRpcAPI
from hastack.openstack.openstack_api.api import SchedulerRpcAPI
import hastack.openstack.openstack_api.db_api as db_api
import hastack.openstack.openstack_constants as openstack_constants
import hastack.openstack.openstack_utils as openstack_utils

from oslo_log import log as logging
from oslo_utils import importutils
import six

_ = has_gettextutils._
_LI = has_gettextutils._LI
_LW = has_gettextutils._LW
_LE = has_gettextutils._LE


CONF = ha_conf.CONF

LOG = logging.getLogger(__name__)


class BasePolicyEngine(object):
    def __init__(self, host, has_driver):
        self.hv_map = {}
        self.compute_api = ComputeAPI()
        self.compute_rpcapi = ComputeRpcAPI()
        self.event_types = {}
        self.scheduler_rpcapi = SchedulerRpcAPI()
        self.notifier = self.compute_api.get_notifier('haservice')
        self.host_driver = importutils.import_object(
                                    CONF.ha_service_hypervisor_driver)
        self.inst_driver = importutils.import_object(
                                    CONF.ha_service_instance_driver)
        self.fencing_driver = importutils.import_object(
                                    CONF.ha_service_fencing_driver)
        self.host_status = {}
        self.reset()
        self._configure_hv_status()

        self.host = host
        # Retrieve the context in a robust manner; self.ctxt is only used
        # during initialization anyway and then the context is retrieved
        # at each periodic task cycle (i.e., to keep it refreshed).
        try:
            self.ctxt = openstack_utils.create_context()
        except Exception as e:
            LOG.warning(_LW("Encountered exception fetching driver extension "
                            "context; falling back to standard admin context; "
                            "exception message is: %(message)s")
                        % {'message': six.text_type(e)})
            self.ctxt = has_driver.get_context()

    def reset(self):
        self.violated_hvs = set()
        self.in_action_hvs = set()
        self.idle_hvs = set()
        self.error_insts = {}

    def _configure_hv_status(self):
        self.start_status = None
        self.migrating_status = None
        self.rebuilding_status = None
        self.end_status = None
        self.error_status = None

    def select_instances(self, context, hv_name):
        raise NotImplementedError()

    def update_hvs_state(self, context):
        """To Do

        Put the hypervisors that violated the policy into the violated list
        and change their status to self.start_status so as to trigger the next
        set of actions on them.
        """
        raise NotImplementedError()

    def update_managed_hvs(self, context, all_hvs):
        raise NotImplementedError()

    def get_moving_insts(self, hv_name):
        raise NotImplementedError()

    def get_move_start_time(self, hv_name, inst_uuid):
        raise NotImplementedError

    def __verify_migration(self, context):
        """Verify

        To make sure HA just verify instances we migrated, the HA service needs
        to perform the following tasks:
        1. Get all resized finished migrations
        2. Iterate over migrations
        3. Get actions of an instance
        4. Check request_id of instance action
        5. If it starts with 'prs-ha-' and it is migrated by HA
        """
        filters = {'status': 'finished'}
        migrations = self.compute_api.query_migration_instances(context,
                                                                filters)
        for mig in migrations:
            if mig['old_instance_type_id'] == mig['new_instance_type_id']:
                actions = self.compute_api.query_instances_actions_by_uuid(
                            context, mig['instance_uuid'])
                if len(actions) > 0:
                    request_id = actions[0]['request_id']
                    if not request_id.startswith(ha_constants.PREFIX_HAS_HA):
                        continue
                inst = self.compute_api.get_instance_by_uuid(
                        context, mig['instance_uuid'],
                        expected_attrs=openstack_constants.
                        INSTANCE_DEFAULT_FIELDS)
                try:
                    self.compute_api.confirm_resize(context, inst)
                    LOG.info(_LI("Successfully confirmed resize of instance "
                                 "%(name)s (%(instance)s).")
                             % {'name': inst.name,
                                'instance': inst.uuid})
                except Exception as ex:
                    LOG.warning(_LW("Failed to confirm resize of instance "
                                "%(name)s (%(instance)s) due to: %(reason)s")
                                % {'name': inst.name,
                                   'instance': inst.uuid,
                                   'reason': six.text_type(ex.message)})

    def select_nodes(self, context):
        """Select nodes that need to evacuate instances.

        TODO: 1,select hosts in avalibiliaty_zone scope
              2,select hosts in host aggregate scope.
              3,select host
              4,select host in a region
        Return all host now.
        """
        all_nodes = self.compute_api.get_all_compute_node(context)

        selected_nodes = all_nodes[:]
        for node in all_nodes:
            if node['hypervisor_type'] == 'ironic':
                selected_nodes.remove(node)

        return selected_nodes

    def fencing_and_evacuate(self, context, node):
        """Fencing and evacuate

        Call the fencing driver to fence the host first and then  move the
        instance on it.
        """
        result = False
        try:
            bmc, user, password = ipmi_utils.get_bmc(node)
            status = ipmi_utils.get_power(node)
            if status != 'off':
                self.fencing_driver.fencing_host(context, bmc, user, password)

            # investigate the force down API seems not force the service down.
            if self.host_driver.hypervisor_is_up(context,
                                                 node['hypervisor_hostname']):
                result = True
                LOG.warning('The host has been shutdown but the service'
                            ' status has not changed to off.')
                return result

            # handle the host which is evacuating

            # if self.host_status.get(node, '') == 'evacuating':
            #    result = True
            #    return result
            # self.host_status[node] = 'evacuating'
            self._rebuild_instances(context, node['hypervisor_hostname'])
            # self.host_status[node] = 'none'
            result = True
        except Exception as e:
            result = True
            LOG.warning(e)
        return result

    def evacuate_instance(self, context, node):
        """Evacuate an instance on a host.

        Leave sanlock to handle brain split
        """
        result = False
        try:
            self._rebuild_instances(context, node['hypervisor_hostname'])
            result = True
        except Exception as e:
            LOG.warning(e)
            result = True
        return result

    def ha_alarm(self, context, node):
        """Just the management network is down, send an alarm."""
        result = False
        LOG.warning('The management network failure.')
        return result

    def noop(self, context, node):
        """Nothing need to be done"""
        result = False
        LOG.info('HAService is working.....')
        return result

    def check_host_power_status(self, context, node):
        """check the host power status and take actions

        :returns: true, has handled, false, need to check in the follow steps
        """
        result = False
        try:
            status = ipmi_utils.get_power(node)
        except Exception as ipmi_exc:
            LOG.warning(_LW("Get IPMI exception for %(node)s "
                            "with reason: %(reason)s")
                        % {'node': node['hypervisor_hostname'],
                           'reason': six.text_type(ipmi_exc)})
            result = True
            return result
        if status != 'on':
            self.evacuate_instance(context, node)
            result = True
        return result

    def service_function(self, context):
        """The engine main function.

        1, Check the power status of all host first. One host with power
        failure will be evacuate the instances on the host and will not be
        checked in the follow steps.

        2, Check the host network status as the power status is OK. Evacuate
        the instance on the host which network status is not OK.

        3, Check the compute process on the host based on the power stauts
        and network status is OK.

        4, Check the instances status as all the above is OK. Restart the
        instance and try to recover.

        :param all_nodes: the detailed info dict of all the nodes in the
                          system
        :param update_hvs_state: update the hypervisors' state if true
        :param do_action: do moving instance action based on hypervisors'
                          state if true

        :returns: None
        """
        # 1) confirm resize the instances which were migrated automatically
        #    by HA/Maintenance
        self.__verify_migration(context)

        selected = self.select_nodes(context)
        ha_service = db_api.get_service_by_host_and_binary(context,
                                                self.host, 'nova-haservice')

        # 2) do HA periodic task
        if not ha_service['disabled']:
            # a, select nodes that need to do ha
            compute_count = len(selected)

            # a, check if we need to do migrate
            service_up_count = 0
            for node in selected:
                service = self.compute_api.get_service_by_compute_host(context,
                                                               node['host'])
                if self.compute_api.service_is_up(service):
                    service_up_count = service_up_count + 1

            if service_up_count < CONF.min_active_compute_percent \
                    * compute_count:
                LOG.warning(_LW("Only %(service_up_count)d compute nodes"
                                "are up, we will disable the HA service.")
                            % {'service_up_count': service_up_count})
                db_api.db_update_service(context,
                                         ha_service['id'],
                                         {'disabled': True})
                return

            # a, monitor the hypervisor and instances
            for node in selected:
                # 1, check the host power status by IPMI and take action
                if self.check_host_power_status(context, node):
                    continue

        else:
            # if service is disabled
            # a, check if all hosts are up
            for node in selected:
                service = self.compute_api.get_service_by_compute_host(context,
                                                               node['host'])
                if not self.compute_api.service_is_up(service):
                    return

            LOG.info("All compute nodes are up, enabling HA service...")

            # a, enable HA service
            db_api.db_update_service(context,
                                     ha_service['id'],
                                     {'disabled': False})
            return

    def _rebuild_instances(self, context, hv_name):
        """Rebuilds instances on a failed hypervisor."""
        inst_tuples = self.select_instances(context, hv_name)
        if not inst_tuples:
            if hv_name not in self.idle_hvs:
                # No more instances to move and we're not idle yet, so this
                # means that we should consider our work done!
                self._action_finished(context, hv_name)
            return

        compute_node = self.hv_map[hv_name]
        htype = compute_node['hypervisor_type']

        # if the hypervisor cannot support 'rebuild' operation, mark
        # the hypervisor to 'error' state.
        if htype in constants.UNSUPPORTED_HYPERVISORS:
            self._action_finished(context, hv_name)
            err_msg = (_LE("The operation failed on the host (%(host)s) "
                         "because its hypervisor (%(hv)s) does not "
                         "support the 'rebuild' operation.")
                         % {'hv': hv_name,
                            'host': compute_node['host']})
            LOG.error(err_msg)
            return

        if hv_name not in self.in_action_hvs:
            self.in_action_hvs.add(hv_name)
            utils.safe_remove(self.idle_hvs, hv_name)

        is_finished = True

        rebuild_states = [openstack_constants.REBUILDING,
                          openstack_constants.REBUILD_SPAWNING,
                          openstack_constants.REBUILD_BLOCK_DEVICE_MAPPING]
        filters = {'task_state': rebuild_states,
                   'host': self.hv_map[hv_name]['host']}
        for inst, action in inst_tuples:
            if hv_name in self.idle_hvs:
                return

            # if the VM is being rebuilt, then we shouldn't try to call rebuild
            # again; otherwise, let's try our best to rebuild it regardless of
            # its task state since the host is dead.
            if inst['task_state'] in rebuild_states:
                is_finished = False
                continue

            # This active/stopped/error state check is imposed
            # by OpenStack, so we check it here to avoid problems calling the
            # evacuate API since we know it would otherwise fail.
            if inst['vm_state'] not in [openstack_constants.ACTIVE,
                                        openstack_constants.STOPPED,
                                        openstack_constants.ERROR]:
                is_finished = False
                LOG.warning(_LW("The system cannot rebuild instance %(name)s "
                            "(%(instance_uuid)s) in the %(state)s state "
                            "because OpenStack restricts the valid initial "
                            "states to active, stopped and error.")
                            % {'name': inst['display_name'],
                               'instance_uuid': inst['uuid'],
                               'state': inst['vm_state']})
                continue

            rebuild_num = len(self.compute_api.query_db_instances(
                              context, filters))
            if rebuild_num >= self.__get_parallel_rebuild(compute_node):
                is_finished = False
                # hit max; no need to look at any more instances this time
                break

            try:
                success = self.__rebuild(context, hv_name, inst)
                if not success:
                    is_finished = False
            except Exception:
                is_finished = False
        if is_finished:
            self._action_finished(context, hv_name)

    def __rebuild(self, context, hv_name, inst):
        """Rebuilds an instance."""
        img = ha_utils.get_image_from_inst(inst)
        request_spec = openstack_utils.build_request_spec(context, img, [inst])
        # set filer working scope
        svc_host = self.hv_map[hv_name]['host']
        filter_properties = {'ignore_hosts': [svc_host]}

        target_hosts = self._get_target_hosts(
            context, ha_constants.HA_ACTION_REBUILD, hv_name)

        if target_hosts:
            filter_properties['force_hosts'] = target_hosts
        # filter_properties[constants.HA_MAINTENANCE_STATUS] = (
        #                                        self.status.get_json())
        scope = constants.FILTER_WORKING_SCOPE_EVACUATE
        request_spec['operation_type'] = scope

        try:
            openstack_utils.setup_instance_group(context, request_spec,
                                                 filter_properties)
            spec_obj = self.compute_api.create_request_spec(context,
                                                            request_spec,
                                                            filter_properties)
            destinations = self.scheduler_rpcapi.select_destinations(
                context, spec_obj)
            host = destinations[0]['host']
            target_hv_name = destinations[0]['nodename']

            # check if the parallel rebuild instances number on the destination
            # host have exceeded the max number; if yes, skip this rebuild
            rebuild_states = [openstack_constants.REBUILDING,
                              openstack_constants.REBUILD_SPAWNING,
                              openstack_constants.REBUILD_BLOCK_DEVICE_MAPPING]
            filters = {'task_state': rebuild_states, 'host': host}
            compute_node = self.hv_map.get(target_hv_name)
            if not compute_node:
                compute_node = self.compute_api.\
                    get_compute_node_by_host_and_nodename(context, host,
                                                          target_hv_name)
            rebuild_num = len(self.compute_api.query_db_instances(
                              context, filters))
            if rebuild_num >= self.__get_parallel_dest_rebuild(compute_node):
                # skip this rebuild and recover ego allocation
                LOG.info(_LI("The HA engine selected destination host "
                             "%(host)s to rebuild %(vm_name)s (%(uuid)s), "
                             "but the host is currently serving as the "
                             "destination host for %(rebuild_num)s rebuild "
                             "operation(s) and can't handle any more; the HA"
                             " engine will wait until the next cycle to try "
                             "and find a valid host for the instance.")
                         % {'host': host, 'vm_name': inst['display_name'],
                            'uuid': inst['uuid'], 'rebuild_num': rebuild_num})
                return False

            inst = self.compute_api.get_instance_by_uuid(
                    context, inst['uuid'],
                    expected_attrs=openstack_constants.INSTANCE_DEFAULT_FIELDS)
            self.compute_api.evacuate(context.elevated(), inst, host, True)
            # if self.get_status(hv_name) != self.rebuilding_status:
            #    self.update_hv_state(context, hv_name, self.rebuilding_status)

            action_info = {'vm_name': inst['display_name'],
                           'vm_uuid': inst['uuid'],
                           'action_name': 'evacuate',
                           'target_host': host}
            self._store_action_info(context, hv_name, action_info)
            LOG.info(_LI("Successfully initiated the rebuild processing for "
                         "instance %(name)s (%(instance)s) on host %(host)s.")
                     % {'name': inst['display_name'],
                        'instance': inst['uuid'],
                        'host': host})
            # Give instance.host a moment to update via RPC for accurate counts
            eventlet.sleep(1)
            return True
        except Exception as ex:
            if isinstance(ex, openstack_constants.NoValidHost):
                # give a more friendly message for NoValidHost cases
                msg = (_LW("Automated rebuild of instance %(name)s "
                         "(%(instance)s) failed because no valid destination "
                         "host(s) could be found. Make sure you have enough "
                         "resources in your relocation domain and try again.")
                       % {'name': inst['display_name'],
                          'instance': inst['uuid']})
            else:
                msg = (_LW("Automated rebuild of instance %(name)s "
                         "(%(instance)s) failed with the following error: "
                         "%(reason)s")
                       % {'name': inst['display_name'],
                          'instance': inst['uuid'],
                          'reason': six.text_type(ex)})
            LOG.warning(msg)
            self.__handle_error(context, hv_name,
                                {'uuid': inst['uuid'],
                                 'name': inst['display_name']}, msg)
            raise

    def _store_event(self, context, hv_name, event_type, extra_msg=None):
        raise NotImplementedError()

    def _store_action_info(self, context, hv_name, action_info):
        return

    def __handle_error(self, context, hv_name, inst_dict, err_msg):
        """Common error handler for the engine to handle retries, etc."""
        inst_uuid = inst_dict['uuid']
        if hv_name not in self.error_insts:
            self.error_insts[hv_name] = {}
        self.error_insts[hv_name].update({inst_uuid:
                 self.error_insts.get(hv_name, {}).get(inst_uuid, 0) + 1})
        if (self.error_insts[hv_name][inst_uuid] >=
                ha_constants.MAX_RETRY_TIMES):
            payload = {'hypervisor_hostname': hv_name,
                       'hypervisor_id': self.hv_map[hv_name]['id'],
                       'instance_uuid': inst_uuid,
                       'error_msg': err_msg}
            self.notifier.info(context,
                               ha_constants.ETYPE_MOVING_INSTANCE_FAILED,
                               payload)
            LOG.warning(_LW('Failed to automatically move instance '
                           '%(name)s (%(inst_uuid)s) away from '
                           '%(hv_name)s; please move it manually.')
                        % {'hv_name': hv_name, 'inst_uuid': inst_uuid,
                           'name': inst_dict['name']})

    def __get_parallel_rebuild(self, compute_node):
        stats = ast.literal_eval(compute_node['stats'] or {})
        return int(stats.get(ha_constants.PARALLEL_REBUILD,
                             ha_constants.DEFAULT_PARALLEL_REBUILD))

    def __get_parallel_dest_rebuild(self, compute_node):
        stats = ast.literal_eval(compute_node['stats'] or {})
        return int(stats.get(ha_constants.PARALLEL_DEST_REBUILD,
                             ha_constants.DEFAULT_PARALLEL_DEST_REBUILD))

    def _should_stop_move(self, context, hv_name):
        raise NotImplementedError()

    def _get_target_hosts(self, context, ha_action, hv_name):
        """When moving instances, specify target hosts."""
        return None

    def move_inst_fail(self, context, hv_name, payload, is_live_migration):
        """Handle the notification send from the nova.

        This method is called when compute service sends notification about
        live-migration roll back or cold migration/rebuild error.

        :param context: OpenStack nova client context
        :param hv_name: the hypervisor name which the instance was moved from
        :param payload: the notification message payload
        :param is_live_migration: True if the instance was live migrated
                                  False if the instance was cold
                                        migrated/rebuild
        :return: None
        """
        inst_id = payload.get('instance_id')
        if (self.error_insts.get(hv_name, {}).get(inst_id, 0) >=
                ha_constants.MAX_RETRY_TIMES):
            # for the rebuild/cold migrate fail case, if sync up logic has
            # done this work, skip it here.
            return
        vmname = payload.get('name')
        inst_hosts = self.get_moving_insts(hv_name)
        msg = (_LW("Automated movement of instance %(vmname)s "
                 "(%(inst_uuid)s) to %(dest)s from %(source)s failed. "
                 "For detailed information about the failure, see the "
                 "nova-compute log file (usually in "
                 "/var/log/nova/nova-compute-%(dest)s.log) for host %(dest)s.")
               % {'inst_uuid': inst_id,
                  'vmname': vmname,
                  'dest': inst_hosts.get(inst_id),
                  'source': hv_name})
        LOG.warning(msg)
        if is_live_migration:
            # for live-migration roll back case, the instance moving lifecycle
            # is over and we should add it into moving_inst so we try to move
            # it in the next cycle.
            utils.safe_remove(self.idle_hvs, hv_name)
            utils.safe_remove(inst_hosts, inst_id)
            self.in_action_hvs.add(hv_name)
        else:
            if hv_name not in self.error_insts:
                self.error_insts[hv_name] = {}
            # if the VM has been automatically cold migrated or evacuated
            # away, even if something wrong occurred on the target host
            # to make the VM enter error state, just log a warnning message
            # since the VM is not on original hypervisor anymore.
            is_away = False
            try:
                inst = self.compute_api.get_instance_by_uuid(context, inst_id,
                                                    expected_attrs=[])
                if inst.node != hv_name:
                    is_away = True
            except openstack_constants.InstanceNotFound:
                # This only happens when the notification about the VM
                # transitioning to the error state lags too much (e.g.,
                # the VM has since been deleted).
                is_away = True
            if is_away:
                utils.safe_remove(inst_hosts, inst_id)
                self.error_insts[hv_name].pop(inst_id, None)
                LOG.warning(_LW("The instance %(vmname)s (%(inst_uuid)s) "
                                "is no longer on hypervisor %(hv_name)s, "
                                "so the engine will not do any action on "
                                "it anymore and take the automated movement "
                                "of the instance as successful one.")
                            % {'inst_uuid': inst_id,
                               'vmname': vmname,
                               'hv_name': hv_name})
                return
            # for rebuild/cold migrate error, the VM has errored out;
            # we should mark the hypervisor as 'error' immediately.
            self.error_insts[hv_name].update({inst_id:
                              ha_constants.MAX_RETRY_TIMES})

        self.__handle_error(context, hv_name,
                 {'uuid': inst_id, 'name': vmname}, msg)

    def get_hv_moving_inst_map(self):
        """Get inst map

        This method returns a dict which the hypervisor name is key and the
        instance uuid list which this engine moved is value.
        """
        hv_moving_inst_map = {}
        for hv_name in self.hv_map:
            moving_insts = self.get_moving_insts(hv_name)
            if moving_insts:
                inst_uuid_list = moving_insts.keys()
                hv_moving_inst_map.update({hv_name: inst_uuid_list})
        return hv_moving_inst_map


class HAEngine(BasePolicyEngine):
    def __init__(self, host, has_driver=None):
        super(HAEngine, self).__init__(host, has_driver)
        self.has_attr_name = 'ha_status'
        # self.event_types = ha_constants.HA_EVENT_TYPES

        # Format: {request_id1: {action_name: xx, vm_name: xx, vm_uuid: xx,
        #                        target_host: xx},
        #          request_id12: {}, ...}
        self.haservice_action = {}

        self.update_managed_hvs(self.ctxt,
                            self.compute_api.get_all_compute_node(self.ctxt))
        # self.__load_hv_state_from_file()

    def reset(self):
        super(HAEngine, self).reset()
        self.current_interval = 0
        self.violated_count = {}

    def _configure_hv_status(self):
        super(HAEngine, self)._configure_hv_status()
        self.start_status = ha_constants.STATE_HA_STARTED
        self.migrating_status = ha_constants.STATE_HA_MIGRATING
        self.rebuilding_status = ha_constants.STATE_HA_REBUILDING
        self.end_status = ha_constants.STATE_HA_EVACUATED
        self.error_status = ha_constants.STATE_HA_ERROR

    def _get_target_hosts(self, context, ha_action, hv_name):
        """When moving instances, specify target hosts."""
        target_host = self.host_driver.get_target_service_host(
            context, ha_action, hv_name)
        return [target_host] if target_host else None

    def update_managed_hvs(self, context, all_nodes):
        """Update state of hypervisors globally or from an aggregate.

        :param context: User context
        :param all_nodes: All host in database
        """
        # reset the hv_map cache
        hv_map = {}

        for node in all_nodes:
            hv_map[node['hypervisor_hostname']] = node

        for hv_name in (set(self.hv_map.keys()) - set(hv_map.keys())):
            utils.safe_remove(self.violated_hvs, hv_name)
            utils.safe_remove(self.violated_count, hv_name)
            utils.safe_remove(self.in_action_hvs, hv_name)
            utils.safe_remove(self.idle_hvs, hv_name)
        self.hv_map = hv_map

    def select_instances(self, context, hv_name):
        inst_tuples = self.inst_driver.select_instances(context, hv_name)
        return inst_tuples

    def move_inst_fail(self, context, hv_name, payload, is_live_migration):
        super(HAEngine, self).move_inst_fail(context, hv_name, payload,
                                             is_live_migration)
        action_info = self.haservice_action.pop(context.request_id, None)
        if action_info:
            action_info['action_result'] = 'failed'
            self._store_event(context, hv_name,
                              ha_constants.ETYPE_HA_ACTION_END, action_info)

    def _store_event(self, context, hv_name, event_type, extra_msg=None):
        extra_msg = extra_msg or {}
        payload = {}
        if event_type != ha_constants.ETYPE_HA_ACTION_END:
            # for has.ha.ha_action.end event type, the related payload
            # should have been stored in self.haservice_action cache; we
            # can get it from the cache.

            payload = {'hypervisor_hostname': hv_name,
                       'hypervisor_id': self.hv_map[hv_name]['id'],
                       'status': "TBD",
                       'policy_type': 'haservice'}
        payload.update(extra_msg)
        if event_type == ha_constants.ETYPE_HA_ACTION_START:
            self.haservice_action[context.request_id] = payload
        self.notifier.info(context, event_type, payload)

    def _store_action_info(self, context, hv_name, action_info):
        self._store_event(context, hv_name, ha_constants.ETYPE_HA_ACTION_START,
                          action_info)

    def _action_finished(self, context, hv_name):
        utils.safe_remove(self.in_action_hvs, hv_name)
        self.idle_hvs.add(hv_name)

    def move_inst_success(self, context):
        action_info = self.haservice_action.pop(context.request_id, None)
        if action_info:
            action_info['action_result'] = 'success'
            self._store_event(context, action_info.get('hypervisor_hostname'),
                              ha_constants.ETYPE_HA_ACTION_END,
                              action_info)
