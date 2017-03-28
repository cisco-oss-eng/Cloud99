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
from cloud99.logging_setup import LOGGER


class TaskStatus(object):
    INIT = "init"
    STOPPED = "stopped"
    ABORTED = "aborted"
    FINISHED = "finished"


class BaseLoader(pykka.ThreadingActor):
    def __init__(self, observer, openrc, inventory, **params):
        # args kept to match signature
        super(BaseLoader, self).__init__()
        self.observer = observer
        self.task_status = TaskStatus.INIT
        self.runner_thread = None
        self.checker_thread = None
        self.times = 0

    def on_receive(self, message):
        msg = message.get('msg')
        params = message.get("params")
        if msg == 'validate_config':
            self.validate_config()
        if msg == 'start':
            self.execute(params)
        if msg == "stop_task":
            self.abort()
        if msg == 'stop':
            self.stop()

    def abort(self):
        self.task_status = TaskStatus.ABORTED
        self.wait_for_threads()
        self.observer.tell({'msg': 'loader_finished', "times": self.times})

    def stop(self):
        self.task_status = TaskStatus.STOPPED
        self.wait_for_threads()
        super(BaseLoader, self).stop()

    def wait_for_threads(self):
        if self.runner_thread:
            self.runner_thread.join()
        if self.checker_thread:
            self.checker_thread.join()
        self.reset()

    def reset(self):
        self.runner_thread = None
        self.checker_thread = None
        self.task_status = TaskStatus.INIT

    def on_failure(self, exception_type, exception_value, traceback):
        LOGGER.error(exception_type, exception_value, traceback)

    @abc.abstractmethod
    def validate_config(self):
        """"""

    @abc.abstractmethod
    def execute(self, params=None):
        """ """

    @abc.abstractmethod
    def load(self, **params):
        """"""

    @abc.abstractmethod
    def check(self, **params):
        """ """
