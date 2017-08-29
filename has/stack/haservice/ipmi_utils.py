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
from oslo_serialization import jsonutils

from pyghmi.ipmi import command

LOG = logging.getLogger(__name__)


def get_bmc(compute_node):
    metrics = compute_node['metrics'] or {}
    metrics = jsonutils.loads(str(metrics))
    bmc = ''
    user = ''
    password = ''
    for metric in metrics:
        if metric.get('name', '') == 'bmc':
            bmc = metric.get('value', '')
        if metric.get('name', '') == 'user':
            user = metric.get('value', '')
        if metric.get('name', '') == 'password':
            password = metric.get('value', '')
    return bmc, user, password


def get_power(compute_node):
    """get a host's power stats by impi"""
    bmc, user, password = get_bmc(compute_node)
    LOG.info(("The bmc info for %(compute_node)s: "
              "bmc: %(bmc)s, user: %(user)s, password: %(password)s")
             % {'compute_node': compute_node['hypervisor_hostname'],
                'bmc': bmc, 'user': user, 'password': "hack_password"})
    ipmicmd = command.Command(bmc=bmc, userid=user, password=password)
    ret = ipmicmd.get_power()
    return ret['powerstate']
