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

from ansible import runner as ansible_runner
from voluptuous import Schema, Required, Optional

from cloud99.logging_setup import LOGGER
from cloud99.monitors import BaseMonitor


class ServiceMonitor(BaseMonitor):
    schema = Schema({
        Required("where"): list,
        Required("with"): str,
        Required("cool_down_time"): int,
        Required("services_to_monitor"): Schema({
            Optional("controller"): list,
            Optional("compute"): list,
        }, extra=True)
    })

    def __init__(self, observer, openrc, inventory, **kwargs):
        super(ServiceMonitor, self).__init__(observer, openrc, inventory,
                                             **kwargs)
        self.services_to_monitor = kwargs["services_to_monitor"]
        self.monitor_command = kwargs["with"]

    def monitor(self):
        self._ping_check()
        self._process_check()
        self._rabbitmq_check()
        time.sleep(self.cool_down_time)
        self.actor_inbox.put({"msg": "monitor"})

    def _get_host_list(self):
        return [host["ip"] for host in self.inventory.itervalues()]

    def _get_hosts_by_role(self, role):
        return filter(lambda host: host["role"] == role,
                      self.inventory.itervalues())

    def _ping_check(self):
        for host_name in self.inventory.keys():
            host = self.inventory[host_name]
            results = ansible_runner.Runner(module_name="ping",
                                            host_list=[host["ip_or_hostname"]],
                                            remote_user=host["username"],
                                            remote_pass=host["password"],
                                            forks=2).run()
            LOGGER.debug(results)

    def _process_check(self):
        for role_name, services in self.services_to_monitor.iteritems():
            for host in self._get_hosts_by_role(role_name):
                for service in services:
                    module_args = self.monitor_command.format(
                        service_name=service)
                    results = ansible_runner.Runner(
                        host_list=[host["ip_or_hostname"]],
                        remote_user=host["username"],
                        remote_pass=host["password"], module_args=module_args,
                        module_name="shell", forks=2).run()
                    LOGGER.debug(results)

    def _rabbitmq_check(self):
        module_args = "sudo rabbitmqctl status"
        for host in self._get_hosts_by_role("controller"):
            results = ansible_runner.Runner(host_list=[host["ip_or_hostname"]],
                                            remote_user=host["username"],
                                            remote_pass=host["password"],
                                            module_args=module_args,
                                            module_name="shell",
                                            forks=2).run()
            LOGGER.debug(results)
