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

from nova import context


class HASDriver(object):
    """Shared driver for HAS services."""
    def get_context(self, ctxt=None, context_service_catalog=None):
        """Method to obtain a context object.

        :param ctxt: Optional context object
        :param context_service_catalog: Optional service catalog

        :returns: An admin context object
        """
        # Get admin context if an admin context was not passed in
        if ctxt is None or not ctxt.is_admin:
            ctxt = context.get_admin_context()
        return ctxt
