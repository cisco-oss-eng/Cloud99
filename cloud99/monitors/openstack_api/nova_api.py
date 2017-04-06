# Copyright 2016 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from novaclient.client import Client
from novaclient.exceptions import ClientException


class NovaHealth(object):
    """
    Provides all the necessary API
    for nova health Check
    """
    def __init__(self, credentials):
        # TODO hardcoded version
        self.novaclient = Client(version="2", **credentials)

    def nova_service_list(self):
        """
        Get the list of nova services
        """
        try:
            service_list = self.novaclient.services.list()
        except (ClientException, Exception) as e:
            return 400, e.message, []
        return 200, "success", service_list

    def nova_stop_server(self, instance_name):
        """
        Stop the server using id
        :param instance_name:
        """
        try:
            server = self.novaclient.servers.find(name=instance_name)
            ret = self.novaclient.servers.stop(server.id)
        except (ClientException, Exception) as e:
            return 400, e.message, []
        return 200, "success", ret

    def nova_start_server(self, instance_name):
        """
        Start the server using id
        :param instance_name:
        """
        try:
            server = self.novaclient.servers.find(name=instance_name)
            ret = self.novaclient.servers.start(server.id)
        except (ClientException, Exception) as e:
            return 400, e.message, []
        return 200, "success", ret
