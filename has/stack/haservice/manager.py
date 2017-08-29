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

"""HA Service"""
import os
import time

from hastack.has.stack import has_gettextutils
from hastack.has.stack.haservice import engine

from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import periodic_task
from oslo_utils import importutils

from threading import Thread

import hastack.has.conf as ha_conf
import hastack.openstack.openstack_utils as openstack_utils

_ = has_gettextutils._

LOG = logging.getLogger(__name__)

CONF = ha_conf.CONF


def period_heartbeat_file(heartbeat_file,
                          heartbeat_interval=CONF.heartbeat_interval_ha):
    """This function will be always running until nova service is terminated.

    It displays nova service alive and working well. Here we don't use
    @periodic_task.periodic_task decorator because the decorator start after
    manager._init_host(), init_host will cost much time we can't expect when
    instances are too many.

    :return: None
    """

    def heartbeat_process():
        while True:
            # create a file in specific directory
            file_path = CONF.heartbeat_file_path + "/%s" % heartbeat_file
            try:
                if not os.path.exists(CONF.heartbeat_file_path):
                    openstack_utils.execute('mkdir', '-p', "%s" %
                                            CONF.heartbeat_file_path,
                                            run_as_root=True)
                if not os.path.isfile(file_path):
                    openstack_utils.execute("touch", file_path,
                                            run_as_root=True)
                time.sleep(heartbeat_interval)
            except Exception as ex:
                # catch all the exception avoiding threading exits
                LOG.error("Write to file failed %s", ex)
                time.sleep(heartbeat_interval)

    heartbeat_thread = Thread(target=heartbeat_process)
    heartbeat_thread.setDaemon(True)
    heartbeat_thread.start()
    LOG.info("Start thread for heartbeat file successfully")


class HAServiceManager(openstack_utils.NovaManager):

    target = messaging.Target(version="1.0")

    """
    The HA manager is responsible for handling the service CRUD operations and
    invoking the periodic tasks.
    """
    def __init__(self, host, has_driver=None, *args, **kwargs):
        super(HAServiceManager, self).__init__(*args, **kwargs)
        self.has_driver = importutils.import_object(CONF.has_driver)
        self.engine = engine.HAEngine(host, self.has_driver)
        # self.maintenance_engine = engine.MaintenanceEngine(None,
        #                                                    self.has_driver)
        period_heartbeat_file("hastack-service.heartbeat",
                              CONF.heartbeat_interval_ha)
        LOG.debug("The engine manager successfully initialized "
                  "the HA service.")

    @periodic_task.periodic_task(spacing=CONF.ha_period_interval)
    def __periodic_task(self, context):
        """This task is triggered every 60 seconds."""
        ctxt = openstack_utils.create_context()
        self.engine.service_function(ctxt)
        # self.maintenance_engine.service_function(ctxt)
