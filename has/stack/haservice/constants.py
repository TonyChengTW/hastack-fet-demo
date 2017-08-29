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

ENABLED = 'enabled'
DISABLED = 'disabled'

# valid values for get_target_service_host(...) HA actions
HA_ACTION_LIVE_MIGRATION = 'live-migration'
HA_ACTION_COLD_MIGRATION = 'cold-migration'
HA_ACTION_REBUILD = 'rebuild'

# keys for metadata
KEY_HAPOLICY = 'haservice'
KEY_ID = 'id'
KEY_NAME = 'name'
KEY_DESC = 'description'
KEY_STATE = 'state'
KEY_RUN_INTERVAL = 'run_interval'
KEY_STABILIZATION = 'stabilization'

KEY_HA_ID = KEY_HAPOLICY + '-' + KEY_ID
KEY_HA_RUN_INTERVAL = KEY_HAPOLICY + '-' + KEY_RUN_INTERVAL
KEY_HA_STABILIZATION = KEY_HAPOLICY + '-' + KEY_STABILIZATION

# ['id', 'name', 'description', 'state', 'run_interval', 'stabilization']
KEYS = [KEY_ID,
        KEY_NAME,
        KEY_DESC,
        KEY_STATE,
        KEY_RUN_INTERVAL,
        KEY_STABILIZATION]

# keys for compute_node_stats table
HYPERVISOR_STATE = 'has:hypervisor_state'
PARALLEL_MIGRATE = 'has:max_parallel_migrations'
PARALLEL_REBUILD = 'has:max_parallel_rebuilds'
PARALLEL_DEST_REBUILD = 'has:max_parallel_dest_rebuilds'

# default parallel values
DEFAULT_PARALLEL_MIGRATE = 5
DEFAULT_PARALLEL_REBUILD = 5

# default number of max parallel rebuild instances on the destination host
DEFAULT_PARALLEL_DEST_REBUILD = 0x7FFFFFFF

# prefix for request_id that HA did
PREFIX_HAS_HA = 'has-ha-'

STATE_OK = 'ok'

STATE_MT_ENTERING = 'entering'
STATE_MT_ON = 'on'
# status for failure mode
STATE_HA_STARTED = 'started'
STATE_HA_MIGRATING = 'migrating'
STATE_HA_REBUILDING = 'rebuilding'
STATE_HA_EVACUATED = 'evacuated'
STATE_HA_ERROR = 'error'
STATE_LIST_HA = [STATE_HA_STARTED, STATE_HA_MIGRATING, STATE_HA_REBUILDING,
                 STATE_HA_EVACUATED, STATE_HA_ERROR]

# max retry times for a single instance
MAX_RETRY_TIMES = 3

ETYPE_HA_STARTED_START = 'has.ha.ha_started.start'
ETYPE_HA_STARTED_END = 'has.ha.ha_started.end'
ETYPE_HA_MIGRATING_START = 'has.ha.ha_migrating.start'
ETYPE_HA_MIGRATING_END = 'has.ha.ha_migrating.end'
ETYPE_HA_REBUILDING_START = 'has.ha.ha_rebuilding.start'
ETYPE_HA_REBUILDING_END = 'has.ha.ha_rebuilding.end'
ETYPE_HA_EVACUATED_START = 'has.ha.ha_evacuated.start'
ETYPE_HA_EVACUATED_END = 'has.ha.ha_evacuated.end'
ETYPE_HA_RECOVERED_START = 'has.ha.ha_recovered.start'
ETYPE_HA_RECOVERED_END = 'has.ha.ha_recovered.end'
ETYPE_HA_ERROR_START = 'has.ha.ha_error.start'
ETYPE_HA_ERROR_END = 'has.ha.ha_error.end'
ETYPE_HA_ALERT = 'has.ha.ha_alert'
ETYPE_HA_ACTION_START = 'has.ha.ha_action.start'
ETYPE_HA_ACTION_END = 'has.ha.ha_action.end'
ETYPE_MOVING_INSTANCE_FAILED = 'has.ha.ha_moving.fail'
