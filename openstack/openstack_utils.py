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
import sys

import hastack.has.conf as ha_conf
import hastack.has.conf.client

from keystoneauth1 import loading as ks_loading

from nova import config as nova_config
import nova.context as nova_context
from nova import manager
from nova import objects
from nova.scheduler import utils as scheduler_utils
from nova import service
from nova import utils as nova_utils
from nova import version

from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

CONF = ha_conf.CONF


def execute(*cmd, **kwargs):
    nova_utils.execute(*cmd, **kwargs)


def create_service(binary=None, topic=None, manager=None):
    nova_config.parse_args(sys.argv)
    logging.setup(CONF, "nova")
    nova_utils.monkey_patch()
    objects.register_all()

    gmr.TextGuruMeditation.setup_autorun(version)

    server = service.Service.create(binary=binary,
                                    topic=topic,
                                    manager=manager)
    service.serve(server)
    service.wait()


def build_request_spec(ctxt, image, instances, instance_type=None):
    return scheduler_utils.build_request_spec(ctxt, image, instances,
                                              instance_type=instance_type)


def setup_instance_group(context, request_spec, filter_properties):
    scheduler_utils.setup_instance_group(context, request_spec,
                                         filter_properties)


def populate_filter_properties(filter_properties, host_state):
    scheduler_utils.populate_filter_properties(filter_properties, host_state)


def instance_sys_meta(instance):
    return nova_utils.instance_sys_meta(instance)


def get_image_from_system_metadata(system_meta):
    return nova_utils.get_image_from_system_metadata(system_meta)


def create_auth_plugin(conf, group_name='DEFAULT'):
    auth_plugin = ks_loading.load_auth_from_conf_options(conf,
                                                         group_name)
    return auth_plugin


def create_client_session(conf, group_name='DEFAULT', **kwargs):
    client_session = ks_loading.load_session_from_conf_options(conf,
                                                               group_name,
                                                               **kwargs)
    return client_session


def create_context():
    group_name = hastack.has.conf.client.CLIENT_GROUP_NAME
    auth_plugin = create_auth_plugin(CONF, group_name)
    kwargs = {'auth': auth_plugin}
    client_session = create_client_session(CONF, group_name, **kwargs)

    # find opts:
    # CLIENT_OPTIONS = ks_loading.get_auth_plugin_conf_options('password')
    # [opt.dest for opt in CLIENT_OPTIONS]
    project_name = CONF[group_name].project_name
    username = CONF[group_name].username
    user_domain_name = CONF[group_name].user_domain_name
    p_domain_name = CONF[group_name].project_domain_name
    access_info = auth_plugin.get_auth_ref(client_session)
    auth_token = access_info.auth_token
    catalog = getattr(access_info.service_catalog, 'catalog', [])
    context = nova_context.RequestContext(user_name=username,
                                          project_name=project_name,
                                          user_domain_name=user_domain_name,
                                          project_domain_name=p_domain_name,
                                          is_admin=True,
                                          read_deleted='no',
                                          user_auth_plugin=auth_plugin,
                                          auth_token=auth_token,
                                          service_catalog=catalog)
    context.service_catalog = v3_to_v2_catalog(context.service_catalog)
    return context


def v3_to_v2_catalog(catalog):
    """Convert a catalog to v2 format.

    X_SERVICE_CATALOG must be specified in v2 format. If you get a token
    that is in v3 convert it.

    :param catalog auth_ref.service_catalog.catalog
    """
    v2_services = []
    for v3_service in catalog:
        # first copy over the entries we allow for the service
        v2_service = {'type': v3_service['type']}
        try:
            v2_service['name'] = v3_service['name']
        except KeyError:  # nosec
            # v3 service doesn't have a name, so v2_service doesn't either.
            pass

        # now convert the endpoints. Because in v3 we specify region per
        # URL not per group we have to collect all the entries of the same
        # region together before adding it to the new service.
        regions = {}
        for v3_endpoint in v3_service.get('endpoints', []):
            region_name = v3_endpoint.get('region')
            try:
                region = regions[region_name]
            except KeyError:
                region = {'region': region_name} if region_name else {}
                regions[region_name] = region

            interface_name = v3_endpoint['interface'].lower() + 'URL'
            region[interface_name] = v3_endpoint['url']

        v2_service['endpoints'] = list(regions.values())
        v2_services.append(v2_service)

    return v2_services


class NovaManager(manager.Manager):
    def __init__(self, *args, **kwargs):
        super(NovaManager, self).__init__(*args, **kwargs)
