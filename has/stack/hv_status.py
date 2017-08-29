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

from oslo_utils import timeutils

from hastack.has.stack.haservice import constants as ha_constants

VERSION = '2.0'


class HypervisorStatus(object):
    def __init__(self, json):
        self.ha_hvs = json['ha']

    def get_ha(self, hv_name):
        """Get ha status of a hypervisor"""
        if hv_name not in self.ha_hvs:
            return ha_constants.STATE_OK
        return self.ha_hvs[hv_name]['state']

    def get_ha_moving_insts(self, hv_name):
        if hv_name not in self.ha_hvs:
            return None
        return self.ha_hvs[hv_name].get('moving_insts')

    def get_ha_moving_inst_start(self, hv_name, inst_uuid):
        if hv_name not in self.ha_hvs:
            return None
        return self.ha_hvs[hv_name].get('inst_start', {}).get(inst_uuid)

    def get_ha_failed_instances(self, hv_name):
        """Get the instances which ha failed to move away."""
        if hv_name not in self.ha_hvs:
            failed_instances = []
        else:
            failed_instances = (self.ha_hvs[hv_name].get('failed_instances') or
                                [])
        return failed_instances

    def set_ha_failed_instances(self, hv_name, inst_uuid_list):
        """Set the instances ha failed to move away for a hypervisor."""
        if hv_name in self.ha_hvs:
            self.ha_hvs[hv_name]['failed_instances'] = inst_uuid_list

    def set_ha(self, hv_name, status):
        """Set ha status to a hypervisor."""
        if status == ha_constants.STATE_OK:
            self.ha_hvs.pop(hv_name)
        else:
            if hv_name in self.ha_hvs:
                self.ha_hvs[hv_name].update(
                                    {'state': status,
                                     'updated_at': timeutils.strtime()})
            else:
                self.ha_hvs[hv_name] = {'state': status,
                                        'created_at': timeutils.strtime(),
                                        'updated_at': timeutils.strtime()}

    def set_ha_moving_insts(self, hv_name, inst_host):
        if hv_name in self.ha_hvs:
            self.ha_hvs[hv_name].update({'moving_insts': inst_host})

    def set_ha_moving_inst_start(self, hv_name, inst_uuid, start):
        if hv_name in self.ha_hvs:
            if 'inst_start' in self.ha_hvs[hv_name]:
                self.ha_hvs[hv_name]['inst_start'].update({inst_uuid: start})
            else:
                self.ha_hvs[hv_name].update({'inst_start':
                                             {inst_uuid: start}})

    def get_ha_timestamp(self, hv_name):
        """Get ha timestamp (created_at, updated_at) of the hypervisor."""
        if hv_name not in self.ha_hvs:
            ha_ts = {'created_at': '-', 'updated_at': '-'}
        else:
            ha_ts = {'created_at': self.ha_hvs[hv_name]['created_at'],
                     'updated_at': self.ha_hvs[hv_name]['updated_at']}
        return ha_ts

    def refresh(self, ha_manage_hosts):
        """Refresh status of all hypervisors

        a. remove non-existent hypervisors from MT
        b. remove non-existent and non-managed hypervisors from HA
        """
        ha_hvs = set(self.ha_hvs.keys())
        for key in ha_hvs - ha_manage_hosts:
            self.ha_hvs.pop(key)
