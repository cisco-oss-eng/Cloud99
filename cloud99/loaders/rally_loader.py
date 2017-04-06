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
import json
import os
import threading
import time

from oslo_config import cfg
from oslo_db import options as db_options
from oslo_db.exception import DBNonExistentTable
from rally import api as rally_api
from rally import consts as rally_consts
from rally.common import db
from rally.cli.commands import deployment as deployment_cli
from rally.cli.commands import task as task_cli
from rally.exceptions import DeploymentNotFound
from rally.exceptions import RallyException
from rally.exceptions import ValidationError
from rally.plugins import load as load_rally_plugins
from sqlalchemy.exc import OperationalError
from voluptuous import Schema, Required, Optional

from cloud99.logging_setup import LOGGER
from cloud99.loaders import BaseLoader

CONF = cfg.CONF


class RallyLoader(BaseLoader):
    schema = Schema({
        Required("scenario_file"): str,
        Optional("scenario_args"): Schema({
            Optional("concurrency"): int,
            Optional("tenant"): int,
            Optional("users_per_tenant"): int,
            Optional("max_concurrency"): int,
            Optional("rps"): int,
            Optional("times"): int,
        }, extra=True),
        Optional("scenario_args_file"): str,
        Required("start_delay"): int,
        Optional("deployment_name"): str,
        Optional("db"): Schema({
            Required("host"): str,
            Required("user"): str,
            Required("password"): str,
            Required("name"): str
        })
    })

    conn_template = "mysql://{user}:{passwd}@{host}/{db_name}"
    # TODO (dratushnyy) this should be configurable
    scenarios_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     "../../../scenarios/rally"))

    def __init__(self, observer, openrc, inventory, **params):
        super(RallyLoader, self).__init__(observer, openrc, inventory,
                                          **params)

        self.scenario_file = os.path.abspath(os.path.join(
            RallyLoader.scenarios_path, params['scenario_file']))

        # TODO (dratushnyy) fallback to default path only if file not found
        self.scenario_args_file = params.get('scenario_args_file', None)
        if self.scenario_args_file:
            self.scenario_args_file = os.path.abspath(os.path.join(
                RallyLoader.scenarios_path, self.scenario_args_file))

        self.start_delay = params['start_delay']
        self.deployment_name = params['deployment_name']
        self.deployment_config = {
            "type": "ExistingCloud",
            "admin": {
                "username": openrc["username"],
                "password": openrc["password"],
                "tenant_name": openrc["tenant_name"]
            },
            "auth_url": openrc["auth_url"],
            "region_name": openrc["region_name"],
            "https_insecure": openrc['https_insecure'],
            "https_cacert": openrc["https_cacert"]
        }
        self.scenario_args = params.get('scenario_args', None)
        # Need to be set to None to avoid exception in stop() method
        self.rally_task = None

        load_rally_plugins()
        if params.get('db'):
            db_connection = RallyLoader.conn_template.format(
                user=params["db"]["user"],
                passwd=params["db"]["pass"],
                host=params["db"]["host"],
                db_name=params["db"]["name"])

            db_options.set_defaults(CONF, connection=db_connection)
        try:
            rally_api.Deployment.get(self.deployment_name)
        except DBNonExistentTable as e:
            db.schema_create()
        except DeploymentNotFound as e:
            try:
                rally_api.Deployment.create(config=self.deployment_config,
                                            name=self.deployment_name)
            except ValidationError as e:
                LOGGER.exception(e)
                raise e
        except OperationalError as e:
            LOGGER.exception(e)
            raise e

        # Since there is no api method to do this - using cli
        deployment_cli.DeploymentCommands().use(self.deployment_name)
        # Using rally task cli to load and validate task
        # TODO check is API support this?
        try:
            self.scenario_config = task_cli.TaskCommands().\
                _load_and_validate_task(self.scenario_file,
                                        json.dumps(self.scenario_args),
                                        self.scenario_args_file,
                                        self.deployment_name)
        except Exception as e:
            LOGGER.exception(e)
            raise e

    def execute(self, params=None):
        if params is None:
            params = {}
        for k, v in params.items():
            for name in self.scenario_config.keys():
                self.scenario_config[name][0]['runner'].update({k: v})

        time.sleep(self.start_delay)
        self.rally_task = rally_api.Task.create(self.deployment_name,
                                                "cloud99")
        self.runner_thread = threading.Thread(name=__name__,
                                              target=self.load)
        self.checker_thread = threading.Thread(name=__name__,
                                               target=self.check)
        LOGGER.debug("Starting task {task_id}".format(
            task_id=self.rally_task.task["uuid"]))
        self.runner_thread.start()
        self.checker_thread.start()

    def validate_config(self):
        try:
            rally_api.Task.validate(self.deployment_name,
                                    self.scenario_config,
                                    task_instance=self.rally_task)
        except Exception as e:
            print(e)
            LOGGER.exception(e)
            self.observer.tell({'msg': 'validation_complete', 'valid': False})
        self.observer.tell({'msg': 'validation_complete', 'valid': True})

    def abort(self):
        try:
            rally_api.Task.abort(self.rally_task.task["uuid"])
        except RallyException as e:
            LOGGER.exception(e)
        finally:
            self.runner_thread.join()
            self.checker_thread.join()
        res = rally_api.Task.get_detailed(self.rally_task.task["uuid"])
        self.times = len(res["results"][0]["data"]["raw"])

        # This will print standard rally report
        task_cli.TaskCommands().detailed(
            task_id=self.rally_task.task['uuid'])
        self.observer.tell({'msg': 'loader_finished', "times": self.times})

    def load(self):
        # wrapper to run actual rally task in separate thread
        # this needed b/c rally_api.Task.start is a blocking call,
        # and the actor thread will not receive any messages while
        # task is running, so it will be not able to abort task execution.
        self.observer.tell({'msg': 'loader_started'})
        rally_api.Task.start(self.deployment_name, self.scenario_config,
                             self.rally_task)

    def check(self):
        while True:
            statuses = [rally_consts.TaskStatus.FINISHED,
                        rally_consts.TaskStatus.FAILED]
            task_status = self.rally_task.get_status(
                self.rally_task.task['uuid'])

            if task_status in statuses:
                self.observer.tell({'msg': 'loader_finished'})
                # This will print standard rally report
                task_cli.TaskCommands().detailed(
                    task_id=self.rally_task.task['uuid'])
                break
            elif task_status == rally_consts.TaskStatus.ABORTED:
                break
            time.sleep(2.0)
