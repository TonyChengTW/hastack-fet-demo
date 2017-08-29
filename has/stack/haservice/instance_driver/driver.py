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

from hastack.has.stack.haservice import driver
from hastack.openstack.openstack_api.api import ComputeAPI
import hastack.openstack.openstack_constants as openstack_constants

compute_api = ComputeAPI()


class HAInstanceDriver(driver.HAInstanceBaseDriver):

    def select_instances(self, context, hv_name):
        """Select all instances from this host

        If you don't have a custom action, set it to None.
        If no instances on this host require HA action, then return [].

        :param context: nova context
        :param svc_host: service host
        :return: [(instance, action)]
        """
        nodes = compute_api.get_compute_nodes_by_hypervisor(context, hv_name)
        for node in nodes:
            if node.hypervisor_hostname == hv_name:
                service = compute_api.get_service_by_compute_host(context,
                                                                  node.host)
                hv_is_up = compute_api.service_is_up(service)
                svc_host = node.host
        states = [openstack_constants.ACTIVE, openstack_constants.STOPPED]
        if not hv_is_up:
            # VMs that are in ERROR state can also be 'rebuilt'
            states.append(openstack_constants.ERROR)

        # For ERROR VM, if its launched_at is None, that means the VM changed
        # to ERROR when booting. This kind of VM cannot be rebuilt.
        # And the VM has 'ha' metadata that will be moved
        expected_attr = {'metadata'}
        insts = [inst for inst in
                 compute_api.get_instance_by_host(context,
                                                  svc_host, expected_attr)
                 if (inst['vm_state'] in states and
                     inst['launched_at'] is not None) and
                     inst['metadata'].get('ha', None) == str(True)]
        return [(inst, None) for inst in insts]
