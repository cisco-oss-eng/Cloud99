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
import abc
import pykka


class BaseMonitor(pykka.ThreadingActor):
    # TODO (dratushnyy) this should be configured with oslo
    COOL_DOWN = 10

    def __init__(self, observer, openrc, inventory, **kwargs):
        super(BaseMonitor, self).__init__()
        self.observer = observer
        self.inventory = {}
        self.openrc = openrc
        # TODO (dratushnyy) add roles support
        if kwargs.get("where"):
            for host_name in kwargs.get("where", []):
                if inventory.get(host_name):
                    self.inventory.update({host_name: inventory[host_name]})

    def on_receive(self, message):
        msg = message["msg"]
        if msg == "stop":
            self.stop()
        if msg == "start":
            self.observer.tell({"msg": "monitor_started"})
            self.monitor()
        if msg == "monitor":
            self.monitor()

    def stop(self):
        self._stop()

    @abc.abstractmethod
    def monitor(self):
        """"""
