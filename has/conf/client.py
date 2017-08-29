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
from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

CLIENT_GROUP_NAME = 'rs_ceilometer'

client_group = cfg.OptGroup(
    CLIENT_GROUP_NAME,
    title='Client Options',
    help="Configuration options for Client")

DEFAULT_AUTH_TYPE = 'password'
DEFAULT_TIMEOUT = 3 * 60

AUTH_TYPE = 'auth_type'
TIMEOUT = 'timeout'


def register_opts(conf):
    conf.register_group(client_group)
    # register session and auth config options
    ks_loading.register_session_conf_options(conf, CLIENT_GROUP_NAME)
    ks_loading.register_auth_conf_options(conf, CLIENT_GROUP_NAME)
    # set default config options
    conf.set_default(AUTH_TYPE, DEFAULT_AUTH_TYPE, group=CLIENT_GROUP_NAME)
    conf.set_default(TIMEOUT, DEFAULT_TIMEOUT, group=CLIENT_GROUP_NAME)


def list_opts():
    return {
        CLIENT_GROUP_NAME: (
            ks_loading.get_session_conf_options() +
            ks_loading.get_auth_common_conf_options() +
            ks_loading.get_auth_plugin_conf_options('password') +
            ks_loading.get_auth_plugin_conf_options('v2password') +
            ks_loading.get_auth_plugin_conf_options('v3password'))
    }
