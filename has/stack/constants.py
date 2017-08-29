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

"""Constants used in HAS component."""

ATTRIBUTE_TYPE_INT = 'int'
ATTRIBUTE_TYPE_STR = 'str'

RESOURCE_GROUP_ALL = 'group_all'
RESOURCE_GROUP_DEFAULT = 'OpenStackHosts'

RPI_KEY_HOST_AGGREGATE_ID = 'host_aggregate_ids'

# Policy related constants
POLICY_ID = 'id'
POLICY_RUN_INTERVAL = 'run_interval'
POLICY_STABILIZATION = 'stabilization'
POLICY_MAX_PARALLEL = 'max_parallel'
POLICY_THRESHOLD = 'threshold'
POLICY_ACTION = 'action'
POLICY_NAME = 'name'
POLICY_DESCRIPTION = 'description'
POLICY_STATE = 'state'
POLICY_GOAL = 'goal'
POLICY_VALID_FLAG = 'is_valid'

POLICY_DELIMITER = '-'
INITIAL_POLICY = 'initialpolicy'
INITIAL_POLICY_ID = INITIAL_POLICY + POLICY_DELIMITER + POLICY_ID

RUNTIME_POLICY = 'runtimepolicy'
RUNTIME_POLICY_ID = RUNTIME_POLICY + POLICY_DELIMITER + POLICY_ID
RUNTIME_POLICY_RUN_INTERVAL = (RUNTIME_POLICY +
                               POLICY_DELIMITER + POLICY_RUN_INTERVAL)
RUNTIME_POLICY_STABILIZATION = (RUNTIME_POLICY +
                                POLICY_DELIMITER + POLICY_STABILIZATION)
RUNTIME_POLICY_MAX_PARALLEL = (RUNTIME_POLICY +
                               POLICY_DELIMITER + POLICY_MAX_PARALLEL)
RUNTIME_POLICY_THRESHOLD = (RUNTIME_POLICY +
                            POLICY_DELIMITER + POLICY_THRESHOLD)
RUNTIME_POLICY_ACTION = RUNTIME_POLICY + POLICY_DELIMITER + POLICY_ACTION

POLICY_KEY_HOST_AGGREGATE_INITIAL = 'host_aggregate_based_initial'
POLICY_KEY_HOST_AGGREGATE_RUNTIME = 'host_aggregate_based_runtime'

MAX_INT_32 = 0x7FFFFFFF
MIN_INT_32 = 0 - MAX_INT_32
MIN_POSITIVE_INT = 1

# Acceptable rtpolicy 'action' values
POLICY_ACTION_MIGRATE_VM = 'migrate_vm'
POLICY_ACTION_MIGRATE_VM_ADVISE_ONLY = 'migrate_vm_advise_only'
POLICY_ACTION_LIST = (POLICY_ACTION_MIGRATE_VM,
                      POLICY_ACTION_MIGRATE_VM_ADVISE_ONLY)

# Runtime policy event constants
PRS_RTPOLICY_HYPERVISOR_ALERT = 'prs.rtpolicy.hypervisor.alert'
PRS_RTPOLICY_HYPERVISOR_VIOLATED = 'prs.rtpolicy.hypervisor.violated'
PRS_RTPOLICY_HYPERVISOR_RECOVERED = 'prs.rtpolicy.hypervisor.recovered'
PRS_RTPOLICY_ACTION_START = 'prs.rtpolicy.action.start'
PRS_RTPOLICY_ACTION_END = 'prs.rtpolicy.action.end'

# Runtime policy optimizer constants
OPTIMIZER_DEFAULT_PRIORITY = 5
# Bit masks for OPTIMIZE_HOSTS return values
OPTIMIZE_HOSTS_PERFORMED_MASK = 0x01
OPTIMIZE_HOSTS_WAIT_MASK = 0x02
# Performed optimization; no further optimizations this cycle
OPTIMIZE_HOSTS_PERFORMED_WAIT = (OPTIMIZE_HOSTS_PERFORMED_MASK |
                                 OPTIMIZE_HOSTS_WAIT_MASK)
# Performed optimization; continue with further optimizations this cycle
OPTIMIZE_HOSTS_PERFORMED_CONTINUE = (OPTIMIZE_HOSTS_PERFORMED_MASK &
                                     ~OPTIMIZE_HOSTS_WAIT_MASK)
# Did not perform optimization; no further optimizations this cycle
OPTIMIZE_HOSTS_NOT_PERFORMED_WAIT = (~OPTIMIZE_HOSTS_PERFORMED_MASK &
                                     OPTIMIZE_HOSTS_WAIT_MASK)
# Did not perform optimization; continue with further optimizations this cycle
OPTIMIZE_HOSTS_NOT_PERFORMED_CONTINUE = (OPTIMIZE_HOSTS_PERFORMED_MASK &
                                         OPTIMIZE_HOSTS_WAIT_MASK)

# HA/MT automatic migration/rebuild will select a target host first, after
# which its ego allocation's resource has changed to target host, and then
# if HA/MT wants to give up this automatic migration/rebuild for condition
# check or exception, notification with 'prs.ha_mt.inst.auto_move.abort'
# event_type would be sent to scheduler service to revert the ego allocation.
EVENT_TYPE_PRS_HA_MT_INST_AUTO_MOVE_ABORT = 'prs.ha_mt.inst.auto_move.abort'

# Filter related constants
FILTER_WORKING_SCOPE_CREATE = 'create'
FILTER_WORKING_SCOPE_LIVE_MIGRATION = 'live-migration'
FILTER_WORKING_SCOPE_COLD_MIGRATION = 'cold-migration'
FILTER_WORKING_SCOPE_RESIZE = 'resize'
FILTER_WORKING_SCOPE_UNSHELVE = 'unshelve'
FILTER_WORKING_SCOPE_EVACUATE = 'evacuate'
FILTER_WORKING_SCOPE_ALL = [FILTER_WORKING_SCOPE_CREATE,
                            FILTER_WORKING_SCOPE_LIVE_MIGRATION,
                            FILTER_WORKING_SCOPE_COLD_MIGRATION,
                            FILTER_WORKING_SCOPE_RESIZE,
                            FILTER_WORKING_SCOPE_UNSHELVE,
                            FILTER_WORKING_SCOPE_EVACUATE]

RES_REQ_CONSUME_PREFIX = 'consume('
RES_REQ_CONSUME_POSTFIX = ')'
RES_REQ_RESERVEON_PREFIX = 'reserveon('
RES_REQ_RESERVEON_POSTFIX = ')'

# Policy engine related constants
# Builtin resource group name
EGO_BUILTIN_RESGROUP = ['InternalResourceGroup',
                        'ComputeHosts',
                        'ManagementHosts',
                        'DockerGroup',
                        RESOURCE_GROUP_DEFAULT]

# Event types
EVENT_TYPE_AGGREGATE_CREATE_END = 'aggregate.create.end'
EVENT_TYPE_AGGREGATE_DELETE_END = 'aggregate.delete.end'
EVENT_TYPE_AGGREGATE_HOST_ADD_END = 'aggregate.addhost.end'
EVENT_TYPE_AGGREGATE_HOST_REMOVE_END = 'aggregate.removehost.end'
EVENT_TYPE_AGGREGATE_METADATA_SET_END = 'aggregate.updatemetadata.end'
EVENT_TYPE_COMPUTE_INST_CREATE_START = 'compute.instance.create.start'
EVENT_TYPE_COMPUTE_TASK_BUILD_INSTANCES = 'compute_task.build_instances'
EVENT_TYPE_SCHEDULER_LIVE_MIG = 'scheduler.live_migration'
EVENT_TYPE_COMPUTE_INST_UPDATE = 'compute.instance.update'
EVENT_TYPE_BUILD_AND_RUN_INST = 'build_and_run_instance'
EVENT_TYPE_PREP_RESIZE = 'prep_resize'
EVENT_TYPE_RESIZE_INST = 'resize_instance'
EVENT_TYPE_FINISH_RESIZE = 'finish_resize'
EVENT_TYPE_UNSHELVE_INST = 'unshelve_instance'
EVENT_TYPE_FINISH_REVERT_RESIZE = 'finish_revert_resize'
EVENT_TYPE_COMPUTE_INST_ROCKBACK_LIVE_MIG_END = (
    'compute.instance._rollback_live_migration.end')
EVENT_TYPE_COMPUTE_INST_LIVE_MIG_ROLLBACK_END = (
    'compute.instance.live_migration._rollback.end')
EVENT_TYPE_COMPUTE_INST_POWERON_END = 'compute.instance.power_on.end'
EVENT_TYPE_COMPUTE_INST_RESUME = 'compute.instance.resume'
EVENT_TYPE_COMPUTE_INST_POWEROFF_END = 'compute.instance.power_off.end'
EVENT_TYPE_COMPUTE_INST_SUSPEND = 'compute.instance.suspend'
EVENT_TYPE_COMPUTE_INST_SHELVE_OFFLOAD_END = (
    'compute.instance.shelve_offload.end')
EVENT_TYPE_COMPUTE_INST_UNSHELVE_END = 'compute.instance.unshelve.end'
EVENT_TYPE_COMPUTE_INST_SHELVE_END = 'compute.instance.shelve.end'
EVENT_TYPE_COMPUTE_INST_IMPORT_END = 'compute.instance.import.end'
EVENT_TYPE_COMPUTE_INST_DELETE_END = 'compute.instance.delete.end'
EVENT_TYPE_COMPUTE_INST_LIVE_MIGRATION_POST_END = (
    'compute.instance.live_migration._post.end')
EVENT_TYPE_COMPUTE_INST_RESIZE_END = 'compute.instance.resize.end'
EVENT_TYPE_COMPUTE_INST_CREATE_END = 'compute.instance.create.end'
EVENT_TYPE_COMPUTE_INST_RESIZE_REVERT_END = (
    'compute.instance.resize.revert.end')
EVENT_TYPE_COMPUTE_INST_UPDATE_SPEC = 'compute.instance.update.spec'
EVENT_TYPE_COMPUTE_INST_LIVE_MIG_PRE_START = (
    'compute.instance.live_migration.pre.start')
EVENT_TYPE_COMPUTE_NODE_CREATE_END = 'compute.node.create.end'
EVENT_TYPE_COMPUTE_NODE_DELETE_END = 'compute.node.delete.end'
EVENT_TYPE_HOST_ENABLE_END = 'HostAPI.set_enabled.end'
EVENT_TYPE_CHECK_MIGRATE_DEST = 'check_can_live_migrate_destination'
EVENT_TYPE_COMPUTE_INST_REBUILD_END = 'compute.instance.rebuild.end'

EVENT_TYPE_SERVERGROUP_CREATE = 'servergroup.create'
EVENT_TYPE_SERVERGROUP_DELETE = 'servergroup.delete'

EVENT_TYPE_SOFT_DELETE_END = 'compute.instance.soft_delete.end'
EVENT_TYPE_RESTORE_END = 'compute.instance.restore.end'

EVENT_TYPE_IDENTITY_PROJECT_CREATED = 'identity.project.created'
EVENT_TYPE_IDENTITY_PROJECT_DELETED = 'identity.project.deleted'

EVENT_TYPE_LIST = [
    EVENT_TYPE_IDENTITY_PROJECT_CREATED,
    EVENT_TYPE_IDENTITY_PROJECT_DELETED,
    EVENT_TYPE_AGGREGATE_CREATE_END,
    EVENT_TYPE_AGGREGATE_DELETE_END,
    EVENT_TYPE_AGGREGATE_HOST_ADD_END,
    EVENT_TYPE_AGGREGATE_HOST_REMOVE_END,
    EVENT_TYPE_AGGREGATE_METADATA_SET_END,
    EVENT_TYPE_COMPUTE_INST_CREATE_START,
    EVENT_TYPE_COMPUTE_TASK_BUILD_INSTANCES,
    EVENT_TYPE_SCHEDULER_LIVE_MIG,
    EVENT_TYPE_COMPUTE_INST_UPDATE,
    EVENT_TYPE_BUILD_AND_RUN_INST,
    EVENT_TYPE_RESIZE_INST,
    EVENT_TYPE_FINISH_REVERT_RESIZE,
    EVENT_TYPE_COMPUTE_INST_ROCKBACK_LIVE_MIG_END,
    EVENT_TYPE_COMPUTE_INST_LIVE_MIG_ROLLBACK_END,
    EVENT_TYPE_COMPUTE_INST_POWERON_END,
    EVENT_TYPE_COMPUTE_INST_RESUME,
    EVENT_TYPE_COMPUTE_INST_POWEROFF_END,
    EVENT_TYPE_COMPUTE_INST_SUSPEND,
    EVENT_TYPE_COMPUTE_INST_IMPORT_END,
    EVENT_TYPE_COMPUTE_INST_DELETE_END,
    EVENT_TYPE_COMPUTE_INST_RESIZE_REVERT_END,
    EVENT_TYPE_COMPUTE_INST_UPDATE_SPEC,
    EVENT_TYPE_COMPUTE_INST_LIVE_MIG_PRE_START,
    EVENT_TYPE_COMPUTE_NODE_CREATE_END,
    EVENT_TYPE_COMPUTE_NODE_DELETE_END,
    EVENT_TYPE_COMPUTE_INST_SHELVE_END,
    EVENT_TYPE_COMPUTE_INST_SHELVE_OFFLOAD_END,
    EVENT_TYPE_COMPUTE_INST_UNSHELVE_END,
    EVENT_TYPE_UNSHELVE_INST,
    EVENT_TYPE_HOST_ENABLE_END,
    EVENT_TYPE_CHECK_MIGRATE_DEST,
    EVENT_TYPE_PREP_RESIZE,
    EVENT_TYPE_FINISH_RESIZE,
    EVENT_TYPE_COMPUTE_INST_RESIZE_END,
    EVENT_TYPE_COMPUTE_INST_CREATE_END,
    EVENT_TYPE_COMPUTE_INST_LIVE_MIGRATION_POST_END,
    EVENT_TYPE_COMPUTE_INST_REBUILD_END,
    EVENT_TYPE_SERVERGROUP_CREATE,
    EVENT_TYPE_SERVERGROUP_DELETE,
    EVENT_TYPE_SOFT_DELETE_END,
    EVENT_TYPE_RESTORE_END,
    EVENT_TYPE_PRS_HA_MT_INST_AUTO_MOVE_ABORT
]

CPU_ALLOCATION_RATIO = 'cpu_allocation_ratio'
RAM_ALLOCATION_RATIO = 'ram_allocation_ratio'
DISK_ALLOCATION_RATIO = 'disk_allocation_ratio'
DEFAULT_CPU_OVER_COMMIT_RATIO = 1.0
DEFAULT_MEM_OVER_COMMIT_RATIO = 1.0
DEFAULT_DISK_OVER_COMMIT_RATIO = 1.0

# All resource state codes as follows
HOST_RES_OK = 0
HOST_RES_UNAVAIL = 1
HOST_RES_CLOSED = 2
HOST_RES_REMOVED = 4

LOST_CONN_CODE = 10500
NOT_ENOUGH_RESOURCES_CODE = 10501

FILTER_ERROR_MESSAGE = ('Platform Resource Scheduler could not find a '
    'suitable host for VM placement or replacement')

ZVM_HYPERVISOR_TYPE = 'zvm'
POWERVM_HYPERVISOR_TYPE = 'powervm'
HYPERV_HYPERVISOR_TYPE = 'hyperv'
DOCKER_HYPERVISOR_TYPE = 'docker'
HYPERVISOR_TYPE_VMWARE_DB = 'VMware vCenter Server'
HYPERVISOR_TYPE_VMWARE_RPI = 'VMware_vCenter_Server'
HYPERVISOR_TYPE_VMWARE_IMAGE = 'vmware'
# Support VMware ESXi host
HYPERVISOR_TYPE_ESX_DB = 'VMware ESXi'
HYPERVISOR_TYPE_ESX_RPI = 'VMware_ESXi'
HYPERVISOR_TYPE_ESX_IMAGE = 'vmware_esx'
HYPERVISOR_TYPE_QEMU = 'QEMU'
IMAGE_ARCH_PPC64 = 'ppc64'
CEILOMETER_CPU_UT_KEY = 'cpu_util'
CPU_UTILIZATION_METRICS_NAME = 'cpu.percent'
CEILOMETER_MEM_UT_KEY = 'mem_util'
MEM_UTILIZATION_METRICS_NAME = 'memory.percent'
INSTANCE_METADATA_CPU_KEY = 'cpu'
INSTANCE_METADATA_MEMORY_KEY = 'memory'
FIXED_UT_MULTIPLE = 100
HOST_CPU_FREQUENCY_METRIC_KEY = "cpu.frequency"

# Hypervisors that don't support rebuilding
UNSUPPORTED_HYPERVISORS = [HYPERV_HYPERVISOR_TYPE, ZVM_HYPERVISOR_TYPE,
                           HYPERVISOR_TYPE_VMWARE_DB]

# Maintenance migration preferences (prs_mt_migration_preferred_order)
MOST_MEM = 'memory_mb.most'
LEAST_MEM = 'memory_mb.least'
MOST_VCPUS = 'vcpus.most'
LEAST_VCPUS = 'vcpus.least'

# Status for VMware
NOT_SUPPORTED = 'Not Supported'
STAND_ALONE = 'stand_alone'
SERVER_GROUP = 'sg'
HEAT = 'heat'
UNDERLINE = '_'
PACKING_POLICY_GOAL = "0-(running_vms+1)"
STRIPING_POLICY_GOAL = "running_vms+1"

RTPOLICY_PREFFIX = "rtpolicy"
INSTANCE_METADATA_FILTER = "InstanceMetadataFilter"
MAINTENANCE_FILTER = "MaintenanceFilter"
VMWARE_DATACENTER_FILTER = "VMwareDataCenterFilter"

HA_MAINTENANCE_STATUS = 'hm_status'
