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

from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.exceptions import ClientException


class KeystoneHealth(object):
    def __init__(self, creds):
        self.keystone_client = keystone_client.Client(**creds)

    def keystone_service_list(self):
        try:
            service_list = self.keystone_client.services.list()
        except (ClientException, Exception) as e:
            return 404, e.message, []
        return 200, "success", service_list

    def keystone_endpoint_find(self, service_type, endpoint_type='publicURL'):
        return self.keystone_client\
            .service_catalog.url_for(service_type=service_type,
                                     endpoint_type=endpoint_type)

    def keystone_return_authtoken(self):
        return self.keystone_client.auth_token
