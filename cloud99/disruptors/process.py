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

import random

import time
from voluptuous import Schema, Required, Any, Optional

from cloud99.disruptors import BaseDisruptor
from cloud99.utils.ssh import SSH
from cloud99.logging_setup import LOGGER


class ProcessDisruptor(BaseDisruptor):
    schema = Schema({
        Required("disrupt"): str,
        Required("where"): list,
        Required("mode"): Any("parallel", "round_robin", "sequential"),
        Required("with"): Schema({
            Required("down_command"): str,
            Optional("down_check"): str,
            Required("up_command"): str,
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

    @staticmethod
    def disrupt_once(disrupt, ip_or_hostname, username, password, start_cmd,
                     stop_cmd, up_check_cmd, down_check_cmd, down_time_min,
                     down_time_max, cool_down_min, cool_down_max):
        LOGGER.debug("Disrupt once {0}".format(ip_or_hostname))
        down_time = random.randint(down_time_min, down_time_max)
        cool_down_time = random.randint(cool_down_min, cool_down_max)
        ssh = SSH(ip_or_hostname, username, password)
        ssh.exec_command(stop_cmd)
        ssh.exec_command(down_check_cmd)  # TODO wait for down
        if start_cmd:  # TODO if service is down
            time.sleep(down_time)
            ssh.exec_command(start_cmd)
        else:
            disruption_finished = False
            elapsed = 0
            while not disruption_finished:
                elapsed += cool_down_min
                result, error = ssh.exec_command(up_check_cmd)
                LOGGER.debug("Up check result is '{0}'. Error is {1}".format(
                    result.strip(), error.strip()))
                if result is not None:
                    result = int(result.strip())
                    disruption_finished = (result == 0)
                # TODO separate param for down_time_max
                if not disruption_finished and elapsed > down_time_max:
                    LOGGER.exception(
                        "{disrupt} on {host} is not up in {timeout}".format(
                            disrupt=disrupt, host=ip_or_hostname,
                            timeout=down_time_max))
                    break
                time.sleep(1)
        time.sleep(cool_down_time)
