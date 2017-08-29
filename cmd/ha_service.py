# copyright (c) 2016 Fiberhome
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

"""Starter script for Nova HA Service."""
import hastack.openstack.openstack_utils as openstack_utils


def main():
    manager = 'hastack.has.stack.haservice.manager.HAServiceManager'
    binary = 'nova-haservice'
    topic = 'haservice'
    openstack_utils.create_service(manager=manager,
                                   binary=binary,
                                   topic=topic)
