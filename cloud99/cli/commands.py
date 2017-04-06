# Copyright 2017 Cisco Systems, Inc.
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

import click
import logging
import yaml

from cloud99.logging_setup import LOGGER, LOG_FILE_HANDLER
from cloud99.main import Cloud99
from cloud99.schemas import validate


@click.group()
@click.option('--debug', default=False, help="Show detailed logging",
              is_flag=True)
@click.option('--rally_debug', default=False,
              help="Show detailed logs from rally", is_flag=True)
@click.pass_context
def cli(ctx, debug, rally_debug):
    if debug:
        LOGGER.setLevel(logging.DEBUG)
    if rally_debug:
        for name in logging.Logger.manager.loggerDict.viewkeys():
            if name.startswith("rally"):
                logging.getLogger(name).setLevel(logging.DEBUG)
                logging.getLogger(name).addHandler(LOG_FILE_HANDLER)


@cli.command("validate_config", short_help="Validates provided yaml")
@click.argument('configuration', type=click.Path(exists=True, dir_okay=False))
def validate_config(configuration):
    with open(configuration, "r") as config_file:
        config = yaml.safe_load(config_file)
        validate(config)


@cli.command("run", short_help="Run tests based on provided configuration")
@click.argument('configuration', type=click.Path(exists=True, dir_okay=False))
def run(configuration):
    cloud99_actor = Cloud99.start(configuration)
    cloud99_actor.proxy().start_tests()
