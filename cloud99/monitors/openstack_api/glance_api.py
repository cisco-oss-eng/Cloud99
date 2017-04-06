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

from glanceclient.v2 import client as glance_client
from glanceclient.exc import ClientException


class GlanceHealth(object):
    def __init__(self, keystone_instance):
        """
        Find the image endpoint
        """
        glance_endpoint = \
            keystone_instance.keystone_endpoint_find(service_type='image')
        token = keystone_instance.keystone_return_authtoken()
        self.glance_client = \
            glance_client.Client(glance_endpoint, token=token)

    def glance_image_list(self):
        try:
            image_list = self.glance_client.images.list()
        except (ClientException, Exception) as e:
            return 404, e.message, []
        return 200, "success", image_list
