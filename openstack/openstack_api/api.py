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

from nova import compute
from nova.compute import rpcapi as compute_rpcapi
from nova import db
from nova import objects
from nova import rpc
from nova.scheduler import rpcapi as scheduler_rpcapi
from nova import servicegroup


class ComputeAPI(object):
    def __init__(self, *args, **kwargs):
        self.compute_api = compute.API()
        self.compute_rpcapi = compute_rpcapi.ComputeAPI()
        self.servicegroup_api = servicegroup.API()

    def live_migrate(self, context, instance, block_migration,
                     disk_over_commit, host_name, **kwargs):
        self.compute_api.live_migrate(context, instance, block_migration,
                                      disk_over_commit, host_name, **kwargs)

    def evacuate(self, context, instance, host, on_shared_storage,
                 admin_password=None):
        self.compute_api.evacuate(context, instance, host, on_shared_storage,
                                  admin_password)

    def confirm_resize(self, context, instance, migration=None):
        self.compute_api.confirm_resize(context, instance, migration)

    def prep_resize(self, ctxt, image, instance, instance_type, host,
                    reservations=None, request_spec=None,
                    filter_properties=None, node=None,
                    clean_shutdown=True):
        self.compute_rpcapi.prep_resize(ctxt, image, instance, instance_type,
                                        host, reservations, request_spec,
                                        filter_properties, node,
                                        clean_shutdown)

    def service_is_up(self, member):
        return self.servicegroup_api.service_is_up(member)

    def get_notifier(service, host=None, publisher_id=None):
        notifier = rpc.get_notifier('haservice', host, publisher_id)
        return notifier

    def query_migration_instances(self, context, filters):
        return objects.MigrationList.get_by_filters(context, filters)

    def query_instances_actions_by_uuid(self, context, instance_uuid):
        return objects.InstanceActionList.get_by_instance_uuid(context,
                                                               instance_uuid)

    def query_db_instances(self, context, filters):
        return objects.InstanceList.get_by_filters(context, filters)

    def get_instance_by_uuid(self, context, uuid,
                             expected_attrs=None):
        if expected_attrs is None:
            expected_attrs = objects.Instance.INSTANCE_DEFAULT_FIELDS
        return objects.Instance.get_by_uuid(context, uuid,
                                            expected_attrs=expected_attrs)

    def get_instance_by_host(self, context, host, expected_attrs=None,
                             use_slave=False):
        return objects.InstanceList.get_by_host(context, host, expected_attrs,
                                                use_slave)

    def get_all_compute_node(self, context):
        return db.compute_node_get_all(context)

    def get_compute_node_by_host_and_nodename(self, context, host, nodename):
        return objects.ComputeNode.get_by_host_and_nodename(context,
                                                            host, nodename)

    def get_compute_nodes_by_hypervisor(self, context, hypervisor):
        return objects.ComputeNodeList.get_by_hypervisor(context, hypervisor)

    def get_service_by_compute_host(self, context, host,
                                    use_slave=False):
        return objects.Service.get_by_compute_host(context, host,
                                                   use_slave=use_slave)

    def get_flavor_by_id(self, context, id):
        return objects.Flavor.get_by_id(context, id)

    def create_request_spec(self, context, request_spec, filter_properties):
        return objects.RequestSpec.from_primitives(context,
                                                   request_spec,
                                                   filter_properties)

    def instance_action_start(self, context, instance_uuid, action_name,
                              want_result=True):
        objects.InstanceAction.action_start(context, instance_uuid,
                                            action_name, want_result)


class ComputeRpcAPI(object):
    def __init__(self, *args, **kwargs):
        super(ComputeRpcAPI, self).__init__(*args, **kwargs)
        self.compute_rpcapi = compute_rpcapi.ComputeAPI()


class SchedulerRpcAPI(object):
    def __init__(self, *args, **kwargs):
        super(SchedulerRpcAPI, self).__init__(*args, **kwargs)
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()

    def select_destinations(self, ctxt, spec_obj):
        return self.scheduler_rpcapi.select_destinations(ctxt, spec_obj)
