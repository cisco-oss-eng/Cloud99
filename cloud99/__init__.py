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

from cloud99.disruptors.dummy import DummyDisruptor
from cloud99.disruptors.host import HostDisruptor
from cloud99.disruptors.process import ProcessDisruptor
from cloud99.loaders.dummy import DummyLoader
from cloud99.loaders.rally_loader import RallyLoader
from cloud99.monitors.dummy import DummyMonitor
from cloud99.monitors.openstackapi import OpenStackApiMonitor
from cloud99.monitors.service import ServiceMonitor
from cloud99.monitors.maria_db import MariaDBMonitor

# TODO loader
ACTOR_CLASSES = {
    "DummyMonitor": DummyMonitor,
    "ServiceMonitor": ServiceMonitor,
    "OpenStackApiMonitor": OpenStackApiMonitor,
    "MariaDBMonitor": MariaDBMonitor,
    "DummyDisruptor": DummyDisruptor,
    "ProcessDisruptor": ProcessDisruptor,
    "HostDisruptor": HostDisruptor,
    "DummyLoader": DummyLoader,
    "Rally": RallyLoader,
}
