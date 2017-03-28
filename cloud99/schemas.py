# Copyright 2017 Cisco Systems, Inc.
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

from voluptuous import Schema, Required, Optional, Invalid

from cloud99 import ACTOR_CLASSES
from cloud99.logging_setup import LOGGER


def validate_openrc(openrc):
    openrc_schema = Schema({
        Required("auth_url"): str,
        Required("username"): str,
        Required("password"): str,
        Required("region_name"): str,
        Required("tenant_name"): str,
        Required("https_cacert"): str,
        Optional("https_insecure"): bool,
    })
    LOGGER.debug("Validating openrc config")
    openrc_schema(openrc)


def validate_inventory(inventory):
    inventory_schema = Schema({
        Required("ip_or_hostname"): str,
        Required("username"): str,
        Required("password"): str,
        Required("role"): str,
    })
    LOGGER.debug("Validating inventory config")
    for host, config in inventory.items():
        inventory_schema(config)


def validate_disruptors(disruptors):
    _validate("disruptors", disruptors)


def validate_loaders(loaders):
    _validate("loaders", loaders)


def validate_monitors(monitors):
    _validate("monitors", monitors)


def _validate(ent_type, ent_list):
    LOGGER.debug("Validating {0} config".format(ent_type))
    for entity in ent_list:
        if type(entity) == str:
            continue
        for class_name, config in entity.items():
            actor_class = ACTOR_CLASSES.get(class_name, None)
            if not actor_class:
                raise Invalid("Unknown {0} {1}".format(ent_type, class_name))
            actor_class.schema(config)


validate = Schema({
    Required("openrc"): validate_openrc,
    Required("inventory"): validate_inventory,
    Required("disruptors"): validate_disruptors,
    Required("loaders"): validate_loaders,
    Required("monitors"): validate_monitors,
})
