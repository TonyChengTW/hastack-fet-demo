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

from oslo_log import log as logging

from hastack.has.stack.haservice import driver
from hastack.openstack.openstack_api.api import ComputeAPI

LOG = logging.getLogger(__name__)

compute_api = ComputeAPI()


class HAHypervisorDriver(driver.HAHypervisorBaseDriver):
    def hypervisor_is_up(self, context, hv_name, **kwargs):
        """Determine if a hypervisor is up.

        If the hypervisor is deemed down, the
        HA service orchestrator will begin its process of evacuating the host.

        :param context: nova context
        :param hv_name: name of a hypervisor
        :return: True if the hypervisor is deemed up and False otherwise
        """
        context = context.elevated()
        nodes = compute_api.get_compute_nodes_by_hypervisor(context, hv_name)
        for node in nodes:
            if node.hypervisor_hostname == hv_name:
                service = compute_api.get_service_by_compute_host(context,
                                                                  node['host'])
                return compute_api.service_is_up(service)
        return False

    def get_target_service_host(self, context, ha_action, hv_name):
        """Get target host

        Provides an extension point for exploiters to specify a target host
        for the specified HA action. The return value should be a valid
        service host that will be ultimately passed to the 'force_hosts'
        scheduling hint.

        :param context: nova context
        :param ha_action: one of live-migration|cold-migration|rebuild
        :param hv_name: hypervisor hostname of the source
        :return: the service host to which the operation should be targeted or
                 None if the scheduler should select
        """
        return None
