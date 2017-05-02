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
import subprocess

import time
from voluptuous import Required, Schema, Optional, Any

from cloud99.disruptors import BaseDisruptor
from cloud99.utils.ssh import SSH
from cloud99.logging_setup import LOGGER


class HostDisruptor(BaseDisruptor):
    schema = Schema({
        Required("where"): list,
        Required("mode"): Any("parallel", "round_robin", "sequential"),
        Required("with"): Schema({
            Required("down_command"): str,
            Optional("down_check"): str,
            Required("up_check"): str,
            Required("times"): int,
            Required("down_time_min"): int,
            Required("down_time_max"): int,
            Required("down_timeout"): int,
            Required("cool_down_min"): int,
            Required("cool_down_max"): int,
            Required("delay"): int,
        })
    })

    # TODO (dratushnyy) this should be configurable
    COOL_DOWN = 60

    def setup_commands(self, **kwargs):
        up_check = kwargs["with"]["up_check"]
        self.up_check = up_check.format(disrupt=self.disrupt)
        down_check = kwargs["with"]["down_check"]
        self.down_check = down_check.format(username=self.disrupt)
        down_command = kwargs.get("with", {}).get("down_command", "")
        self.stop_cmd = down_command.format(disrupt=self.disrupt)
        start_command = kwargs.get("with", {}).get("up_command", "")
        self.start_cmd = start_command.format(disrupt=self.disrupt)

    @staticmethod
    def disrupt_once(disrupt, ip_or_hostname, username, password, start_cmd,
                     stop_cmd, up_check_cmd, down_check_cmd, down_time_min,
                     down_time_max, cool_down_min, cool_down_max):
        # TODO (dratushnyy) named params in format
        check_cmd = up_check_cmd.format(username=username, host=ip_or_hostname)
        check_cmd = check_cmd.split(" ")
        ssh = SSH(ip_or_hostname, username, password)
        ssh.exec_command(stop_cmd)
        disruption_finished = False
        elapsed = 0
        while not disruption_finished:
            time.sleep(HostDisruptor.COOL_DOWN)
            elapsed += HostDisruptor.COOL_DOWN
            disruption_finished = (subprocess.call(check_cmd) == 0)

            if not disruption_finished and elapsed > down_time_max:
                LOGGER.exception("Host {host} not up in {timeout}".format(
                    host=ip_or_hostname, timeout=down_time_max
                ))
                break
        time.sleep(cool_down_max)
