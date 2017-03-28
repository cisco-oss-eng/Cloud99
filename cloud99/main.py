# Copyright 2016 Cisco Systems, Inc.
# All Rights R6served.
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

import copy
import pykka
import warnings
import yaml

from cloud99 import ACTOR_CLASSES
from cloud99.logging_setup import LOGGER_NAME
import logging
LOGGER = logging.getLogger(LOGGER_NAME)

warnings.filterwarnings("ignore")


class Cloud99(pykka.ThreadingActor):
    def __init__(self, config_file):
        super(Cloud99, self).__init__()
        with open(config_file) as config_yam:
            self.config = dict(yaml.safe_load(config_yam))
        self.monitors_to_start = len(self.config.get("monitors"))
        self.monitors = []
        self.loaders_to_start = len(self.config.get("loaders"))
        self.loaders_to_wait = 0
        self.loaders = []
        self.disruptors = []
        self.disruptors_to_wait = len(self.config.get("disruptors"))
        self.clean_run = False

    def start_tests(self):
        self.create_all("monitors")
        self.create_all("loaders")
        self.create_all("disruptors")
        self.actors_perform_command("monitors", "start")

    def on_receive(self, message):
        LOGGER.debug("On receive: {}".format(message))
        msg = message.get("msg")
        if msg == "monitor_started":
            self.monitors_to_start -= 1
            LOGGER.debug("{count} monitor(s) left to start".format(
                count=self.monitors_to_start))
            if self.monitors_to_start <= 0:
                self.actors_perform_command("loaders", "start",
                                            {"times": 10000})  # TODO
        elif msg == "loader_started":
            # TODO better check
            self.loaders_to_start -= 1
            self.loaders_to_wait += 1
            LOGGER.debug("{count} Loader(s) left to start".format(
                count=self.loaders_to_start))
            if self.loaders_to_start <= 0 and not self.clean_run:
                LOGGER.debug("Starting all disruptors.")
                self.actors_perform_command("disruptors", "start")

        elif msg == "loader_finished":
            self.loaders_to_wait -= 1
            LOGGER.debug("Loader finished. Loaders to wait {count}".format(
                count=self.loaders_to_wait
            ))
            if self.loaders_to_wait <= 0:
                if not self.clean_run:
                    self.clean_run = True
                    self.loaders_to_start = len(self.config.get("loaders"))
                    self.loaders_to_wait = 0
                    # This is tmp. TODO (dratushnyy) better way for params
                    times = message.get("times") or 10
                    LOGGER.debug("Starting clean run: no disruption. "
                                 "Times is {times}".format(times=times))
                    self.actors_perform_command("loaders", "start",
                                                {"times": times})
                else:
                    self.stop()

        elif msg == "disruption_finished":
            self.disruptors_to_wait -= 1
            LOGGER.debug("Disruptors to wait {0}".format(
                self.disruptors_to_wait))
            if self.disruptors_to_wait <= 0:
                LOGGER.debug("Disruption is finished")
                self.actors_perform_command("loaders", "stop_task")

    def create_all(self, actor_type):
        LOGGER.debug("Creating all {actors}.".format(actors=actor_type))
        openrc = copy.deepcopy(self.config["openrc"])
        inventory = copy.deepcopy(self.config["inventory"])
        for actor in self.config[actor_type]:
            # TODO (dratushnyy) support actor without params (list)
            for actor_class, actor_params in actor.items():
                try:
                    actor_class = ACTOR_CLASSES.get(actor_class)
                    actor_ref = actor_class.start(self.actor_ref, openrc,
                                                  inventory, **actor_params)
                    actor_collection = getattr(self, actor_type)
                    actor_collection.append(actor_ref)
                    msg = "Actor started, actor class {actor_class}, " \
                          "actor params {params}" \
                        .format(class_name=actor_class,
                                actor_class=actor_class, params=actor_params)
                    LOGGER.debug(msg)
                except Exception as e:
                    LOGGER.exception(e)
                    self.stop()

        LOGGER.debug("All {actors} are created.".format(actors=actor_type))

    def stop(self):
        self.stop_all("disruptors")
        self.stop_all("loaders")
        self.stop_all("monitors")
        super(Cloud99, self).stop()

    def stop_all(self, actor_type):
        actor_collection = getattr(self, actor_type)
        LOGGER.debug("Stopping all {actors}.".format(actors=actor_type))
        for actor in actor_collection:
            if actor.is_alive():
                LOGGER.debug("Stopping {actor}".format(actor=actor))
                actor.ask({"msg": "stop"})
                LOGGER.debug("Stopped {actor}".format(actor=actor))

        for actor in actor_collection:
            if actor.is_alive():
                LOGGER.error("Actor {actor} is still alive"
                             .format(actor=actor))
        LOGGER.debug("All {actors} stopped.".format(actors=actor_type))
        setattr(self, actor_type, [])

    def alive(self, actor_type):
        actor_collection = getattr(self, actor_type)
        alive = False
        for actor_ref in actor_collection:
            alive = actor_ref.is_alive()
        return alive

    def actors_perform_command(self, actor_type, command, params=None):
        LOGGER.debug("Sending {command} to all {actors}".format(
            command=command, actors=actor_type))
        actor_collection = getattr(self, actor_type)
        for actor_ref in actor_collection:
            actor_ref.tell({"msg": command, "params": params})
            LOGGER.debug("Sent {command} to {actor}".format(
                command=command, actor=actor_ref))

    def actors_perform_command_seq(self, actor_type, command):
        actor_collection = getattr(self, actor_type)
        for actor_ref in actor_collection:
            if actor_ref.is_alive():
                actor_ref.ask({"msg": command})
