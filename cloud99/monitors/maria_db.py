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
from voluptuous import Schema, Required

from cloud99.logging_setup import LOGGER
from cloud99.monitors import BaseMonitor


class MariaDBMonitor(BaseMonitor):
    schema = Schema({
        Required("where"): list,
        Required("cool_down_time"): int,
        Required("db_password"): str,
        Required("db_user"): str,
    })

    def __init__(self, observer, openrc, inventory, **kwargs):
        super(MariaDBMonitor, self).__init__(observer, openrc, inventory,
                                             **kwargs)
        self.db_user = kwargs["db_user"]
        self.db_password = kwargs["db_password"]

    def monitor(self):
        self._mariadb_check()
        time.sleep(self.cool_down_time)
        self.actor_inbox.put({"msg": "monitor"})

    def _mariadb_check(self):
        module_args = "mysql -u{} -p{} -e \"show databases;\"" \
                      "| grep nova".format(self.db_user, self.db_password)
        for host_name in self.inventory.keys():
            host_data = self.inventory[host_name]
            results = ansible_runner.Runner(
                host_list=[host_data["ip_or_hostname"]],
                remote_user=host_data["username"],
                remote_pass=host_data["password"],
                module_args=module_args, module_name="shell", forks=2).run()
            LOGGER.debug(results)
