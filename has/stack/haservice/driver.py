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


class HAHypervisorBaseDriver(object):
    """Driver for HA service to load hypervisors and instances

    exploiters should to implement this to write their own driver.
    """
    def __init__(self, *args, **kwargs):
        pass

    def select_hypervisors(self, context, aggregate_id=None):
        """select hypervisor

        Determine which hosts are deemed inactive and potential candidates
        for HA.

        :param context: nova context
        :param aggregate_id: ID of aggregate; None if no aggregate
        :return: [hypervisorname]
        """
        raise NotImplementedError()

    def hypervisor_is_up(self, context, hv_name, **kwargs):
        """Determine if a hypervisor is up.

        If the hypervisor is deemed down, the
        HA service orchestrator will begin its process of evacuating the host.

        :param context: nova context
        :param hv_name: name of a hypervisor
        :return: True if the hypervisor is deemed up and False otherwise
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def can_enter_maintenance(self, context, hv_name):
        """Determine if a hypervisor can enter maintenance mode.

        This method is only called when the user tries to
        enable maintenance mode for a host.

        :param context: nova context
        :param hv_name: name of a hypervisor
        :return: (boolean, reason)
        """
        raise NotImplementedError()


class HAInstanceBaseDriver(object):
    """Driver for HA service to load instances;

    exploiters should implement this to write their own driver.
    """
    def __init__(self, *args, **kwargs):
        pass

    def select_instances(self, context, svc_host, hv_is_up):
        """Select all instances from this host

        If you don't have a custom action, set it to None.
        If no instances on this host require HA action, then return [].

        :param context: nova context
        :param svc_host: service host
        :param hv_is_up: True if the hypervisor is active and False otherwise
        :return: [(instance, action)]
        """
        raise NotImplementedError()


class HAFencingBaseDriver(object):
    """Driver for HA service to fencing host"""
    def __init__(self, *args, **kwargs):
        pass

    def fencing_host(self, context, svc_host):
        """Fencing host from the environment.

        :param context: nova context
        :param svc_host: service host
        :param hv_is_up: True if the hypervisor is active and False otherwise
        :return: [(instance, action)]
        """
        raise NotImplementedError()
