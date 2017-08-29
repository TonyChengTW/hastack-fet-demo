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
from pyghmi.ipmi import command

from hastack.has.stack.haservice import driver


LOG = logging.getLogger(__name__)


class HAFencingDriver(driver.HAFencingBaseDriver):

    def fencing_host(self, context, svc_host):
        """Openstack force host down fencing driver.

        :param context: nova context
        :param svc_host: service host
        :param hv_is_up: True if the hypervisor is active and False otherwise
        :return: [(instance, action)]
        """
        pass


class IPMIFencingDriver(driver.HAFencingBaseDriver):
    def fencing_host(self, context, bmc, user, password):
        """Fencing the host by IPMI"""
        ipmicmd = command.Command(bmc=bmc, userid=user, password=password)
        ipmicmd.set_power('off')
