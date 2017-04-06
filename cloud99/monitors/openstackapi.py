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

import time

from voluptuous import Schema, Required

from cloud99.logging_setup import LOGGER
from cloud99.monitors import BaseMonitor
from cloud99.monitors.openstack_api import cinder_api
from cloud99.monitors.openstack_api import glance_api
from cloud99.monitors.openstack_api import keystone_api
from cloud99.monitors.openstack_api import neutron_api
from cloud99.monitors.openstack_api import nova_api


class OpenStackApiMonitor(BaseMonitor):
    schema = Schema({
        Required("cool_down_time"): int
    })

    def __init__(self, observer, openrc, inventory, **kwargs):
        super(OpenStackApiMonitor, self).__init__(observer, openrc, inventory,
                                                  **kwargs)

        self.keystone = keystone_api.KeystoneHealth(self.openrc)
        self.neutron = neutron_api.NeutronHealth(self.openrc)
        self.glance = glance_api.GlanceHealth(self.keystone)
        password = self.openrc.pop("password")
        project_id = self.openrc["tenant_name"]
        self.openrc.update({"project_id": project_id, "api_key": password})
        self.nova = nova_api.NovaHealth(self.openrc)
        self.cinder = cinder_api.CinderHealth(self.openrc)
        self.cool_down_time = kwargs.get("cool_down_time",
                                         BaseMonitor.COOL_DOWN)

    def monitor(self):
        self.keystone_check()
        self.neutron_check()
        self.nova_check()
        self.glance_check()
        self.cinder_check()
        time.sleep(self.cool_down_time)
        self.actor_inbox.put({"msg": "monitor"})

    def keystone_check(self):
        status, message, service_list = self.keystone.keystone_service_list()
        LOGGER.debug("{} reply '{}' Message '{}' Service list '{}'"
                     .format("Keystone", status, message, service_list))

    def neutron_check(self):
        status, message, service_list = self.neutron.neutron_agent_list()
        LOGGER.debug("{} reply '{}' Message '{}' Agents list '{}'"
                     .format("Neutron", status, message, service_list))

    def nova_check(self):
        status, message, service_list = self.nova.nova_service_list()
        LOGGER.debug("{} reply '{}' Message '{}' Service list '{}'"
                     .format("Nova", status, message, service_list))

    def glance_check(self):
        status, message, image_list = self.glance.glance_image_list()
        LOGGER.debug("{} reply '{}' Message '{}' Image list '{}'"
                     .format("Glance", status, message, image_list))

    def cinder_check(self):
        status, message, cinder_list = self.cinder.cinder_list()
        LOGGER.debug("{} reply '{}' Message '{}' Cinder list '{}'"
                     .format("Cinder", status, message, cinder_list))
