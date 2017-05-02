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
import threading
import time
import pykka

from cloud99.logging_setup import LOGGER


class DisruptMode(object):
    PARALLEL = "parallel"
    ROUND_ROBIN = "round_robin"
    SEQUENTIAL = "sequential"


def round_robin_disruption(disrupt, nodes, start_cmd, stop_cmd, up_check_cmd,
                           down_check_cmd, down_time_min, down_time_max,
                           cool_down_min, cool_down_max, total, disrupt_func):
    iteration = 1
    while iteration <= total:
        for host_name, host_info in nodes.items():
            LOGGER.debug("HOST: {host} Iteration {iteration} of {total}".
                         format(host=host_info["ip_or_hostname"],
                                iteration=iteration, total=total))
            disrupt_func(disrupt, host_info["ip_or_hostname"],
                         host_info["username"], host_info["password"],
                         start_cmd, stop_cmd, up_check_cmd,
                         down_check_cmd, down_time_min, down_time_max,
                         cool_down_min, cool_down_max)
        iteration += 1


def sequential_disruption(disrupt, nodes, start_cmd, stop_cmd, up_check_cmd,
                          down_check_cmd, down_time_min, down_time_max,
                          cool_down_min, cool_down_max, total, disrupt_func):

    for host_name, host_info in nodes.items():
        iteration = 1
        while iteration <= total:
            LOGGER.debug("HOST: {host} Iteration {iteration} of {total}. "
                         "Node info node={node}".
                         format(host=host_info["ip_or_hostname"],
                                iteration=iteration, total=total,
                                node=host_info))
            disrupt_func(disrupt, host_info["ip_or_hostname"],
                         host_info["username"], host_info["password"],
                         start_cmd, stop_cmd, up_check_cmd,
                         down_check_cmd, down_time_min, down_time_max,
                         cool_down_min, cool_down_max)
            iteration += 1


def parallel_disruption(disrupt, nodes, start_cmd, stop_cmd, up_check_cmd,
                        down_check_cmd, down_time_min, down_time_max,
                        cool_down_min, cool_down_max, total, disrupt_func):
    threads = []
    for host_name, host_info in nodes.items():
        thread = threading.Thread(
            target=sequential_disruption, group=None,
            name="{}:{}".format(host_name, stop_cmd),
            args=(disrupt, {host_name: host_info}, start_cmd, stop_cmd,
                  up_check_cmd, down_check_cmd, down_time_min, down_time_max,
                  cool_down_min, cool_down_max, total, disrupt_func))
        thread.start()
        threads.append(thread)
    [t.join() for t in threads]


class BaseDisruptor(pykka.ThreadingActor):

    def __init__(self, observer, openrc, inventory, **kwargs):
        super(BaseDisruptor, self).__init__()
        self.observer = observer
        self.mode = kwargs["mode"]
        self.disruption_count = kwargs["with"]["times"]
        self.disrupt = kwargs.get("disrupt")
        self.delay = kwargs["with"]["delay"]
        self.down_time_min = kwargs["with"]["down_time_min"]
        self.down_time_max = kwargs["with"]["down_time_max"]
        self.cool_down_min = kwargs["with"]["cool_down_min"]
        self.cool_down_max = kwargs["with"]["cool_down_max"]
        self.up_check = ""
        self.down_check = ""
        self.stop_cmd = ""
        self.start_cmd = ""

        self.hosts = {}
        # TODO (dratushnyy) add support for roles
        for host_name in kwargs["where"]:
            if inventory.get(host_name):
                self.hosts.setdefault(host_name, inventory[host_name])
        self.inventory = inventory
        self.setup_commands(**kwargs)

    def setup_commands(self, **kwargs):
        up_check = kwargs["with"]["up_check"]
        self.up_check = up_check.format(disrupt=self.disrupt)
        down_check = kwargs["with"]["down_check"]
        self.down_check = down_check.format(disrupt=self.disrupt)
        down_command = kwargs.get("with", {}).get("down_command", "")
        self.stop_cmd = down_command.format(disrupt=self.disrupt)
        start_command = kwargs.get("with", {}).get("up_command", "")
        self.start_cmd = start_command.format(disrupt=self.disrupt)

    def on_receive(self, message):
        msg = message.get("msg")
        if msg == "start" or msg == "disrupt":
            self.disruption()
        if msg == "stop":
            self.stop()

    def disruption(self):
        self.observer.tell({"msg": "disruption_started", "self": self})
        time.sleep(self.delay)
        if self.mode == DisruptMode.PARALLEL:
            parallel_disruption(
                self.disrupt, self.hosts, self.start_cmd,
                self.stop_cmd, self.up_check, self.down_check,
                self.down_time_min, self.down_time_max,
                self.cool_down_min, self.cool_down_max,
                self.disruption_count, self.disrupt_once)
        elif self.mode == DisruptMode.ROUND_ROBIN:
            round_robin_disruption(
                self.disrupt, self.hosts, self.start_cmd,
                self.stop_cmd, self.up_check, self.down_check,
                self.down_time_min, self.down_time_max,
                self.cool_down_min, self.cool_down_max,
                self.disruption_count, self.disrupt_once)
        elif self.mode == DisruptMode.SEQUENTIAL:
            sequential_disruption(
                self.disrupt, self.hosts, self.start_cmd,
                self.stop_cmd, self.up_check, self.down_check,
                self.down_time_min, self.down_time_max,
                self.cool_down_min, self.cool_down_max,
                self.disruption_count, self.disrupt_once)
        self.observer.tell({"msg": "disruption_finished", "self": self})
        self.stop()

    @staticmethod
    @abc.abstractmethod
    def disrupt_once(disrupt, ip_or_hostname, username, password, start_cmd,
                     stop_cmd, up_check_cmd, down_check_cmd, down_time_min,
                     down_time_max, cool_down_min, cool_down_max):
        """"""
