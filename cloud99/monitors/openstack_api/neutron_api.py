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

from neutronclient.v2_0 import client as neutron_client
from neutronclient.common.exceptions import NeutronException


class NeutronHealth(object):

    def __init__(self, creds):
        self.neutron_client = neutron_client.Client(**creds)

    def neutron_agent_list(self):
        try:
            agent_list = self.neutron_client.list_agents()
        except (NeutronException, Exception) as e:
            return 404, e.message, []
        return 200, "success", agent_list['agents']
