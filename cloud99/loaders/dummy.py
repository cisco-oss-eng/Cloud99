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

import threading
import time

from voluptuous import Schema

from cloud99.logging_setup import LOGGER
from cloud99.loaders import BaseLoader, TaskStatus


class DummyLoader(BaseLoader):
    # TODO (dratushnyy) this should be configurable
    COOL_DOWN = 10
    schema = Schema({}, extra=True)

    def validate_config(self):
        self.observer.tell({"msg": "validation_complete", "valid": True})

    def execute(self, params=None):
        if params and params.get("times"):
            self.times = params.get("times")
        self.runner_thread = threading.Thread(name=__name__,
                                              target=self.load)
        self.checker_thread = threading.Thread(name=__name__,
                                               target=self.check)
        self.runner_thread.start()
        self.checker_thread.start()
        self.observer.tell({"msg": "loader_started", "self": self})

    def load(self):
        count = 0
        while True:
            if self.task_status == TaskStatus.ABORTED:
                self.times = count
                break
            count += 1
            if count >= self.times:
                self.task_status = TaskStatus.FINISHED
                break
            LOGGER.debug("Iteration {count} of {times}".format(
                count=count, times=self.times
            ))
            time.sleep(DummyLoader.COOL_DOWN)

    def check(self):
        while True:
            if self.task_status == TaskStatus.ABORTED:
                break

            if self.task_status == TaskStatus.FINISHED:
                self.observer.tell({"msg": "loader_finished",
                                    "self": self,
                                    "times": self.times})
                break
            time.sleep(2.0)
