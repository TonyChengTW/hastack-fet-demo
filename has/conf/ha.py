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
import hastack.has.stack.constants as constants
from oslo_config import cfg

ha_period_interval = [
    cfg.IntOpt('ha_period_interval',
               default=30,
               help='The period interval of the hastack service'
                    ' to check the compute power status.')
]
heartbeat_ha_opts = [
    cfg.StrOpt('heartbeat_file_path',
               default='/etc/watchdog/zombie/',
               help='The store of heartbeat file'),
    cfg.IntOpt('heartbeat_interval_ha',
               default=5,
               help='heartbeat interval of VM HA')
]
driver_opts = [
    cfg.StrOpt('ha_service_hypervisor_driver',
               default='hastack.has.stack.haservice.hypervisor_driver'
                       '.driver.HAHypervisorDriver',
               help='The default driver for HA service to get failed '
                    'hypervisors'),
    cfg.StrOpt('ha_service_instance_driver',
               default='hastack.has.stack.haservice.instance_driver.driver.'
                       'HAInstanceDriver',
               help='The default driver for the HA service to get instances '
                    'to migrate or rebuild'),
    cfg.StrOpt('ha_service_fencing_driver',
               default='hastack.has.stack.haservice.fencing_driver.driver.'
                       'IPMIFencingDriver',
               help='The default driver for the HA service to get instances '
                    'to migrate or rebuild')
]
maintenance_migrate_retry = [
    cfg.BoolOpt('maintenance_migrate_retry',
                default=False,
                help='Whether retry when migration failed in maintenance '
                       'mode.')
]
min_active_compute_percent = [
    cfg.FloatOpt('min_active_compute_percent',
               default=0.3,
               help='The default minimum percent of active compute nodes '
                    'to disable the service')
]

has_ha_mt_options = [
    cfg.IntOpt('has_ha_timeout_seconds',
               default=1200,
               help='The length of time (in seconds) within which a '
               'live migration, cold migration or rebuild operation needs to '
               'finish per VM before the overall operation state moves '
               'to the error state.'),
    cfg.StrOpt('has_mt_migration_preferred_order',
               default=constants.MOST_MEM,
               help='The preferred order in which VM migrations will be '
               'attempted for maintenance mode operations; valid values '
               'include %(most-mem)r (default), %(least-mem)r, %(most-vcpus)r '
               'or %(least-vcpus)r' % {'most-mem': constants.MOST_MEM,
                                       'least-mem': constants.LEAST_MEM,
                                       'most-vcpus': constants.MOST_VCPUS,
                                       'least-vcpus': constants.LEAST_VCPUS}),
    cfg.StrOpt('has_compute_status_file',
               default='/etc/hastack.has_compute_node_status.json',
               help='Compute node stats file')
]

has_common_opts = [
    cfg.BoolOpt('service_per_host_aggregate',
               default=False,
               help='True to enable host aggregate based policy mode; '
               'False to switch to global policy mode')
]

has_driver_options = [
    cfg.StrOpt('has_driver',
               default='hastack.has.stack.has_driver.HASDriver',
               help='The default HAS extension point to be shared '
                    'across HAS services')
]


ALL_OPTS = (ha_period_interval +
            heartbeat_ha_opts +
            driver_opts +
            maintenance_migrate_retry +
            min_active_compute_percent +
            has_ha_mt_options +
            has_common_opts +
            has_driver_options)


def register_opts(conf):
    conf.register_opts(ALL_OPTS)


def list_opts():
    return {"DEFAULT": ALL_OPTS}
