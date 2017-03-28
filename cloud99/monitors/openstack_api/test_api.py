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

import argparse
import logging

from keystoneclient.v3 import credentials

import cinder_api
import glance_api
import keystone_api
import neutron_api
import nova_api


def nova_endpoint_check(nova_instance):
    status, message, service_list = nova_instance.nova_service_list()
    if status == 200:
        for service in service_list:
            cpulse_log.debug("Binary=%s Host=%s Zone=%s Status=%s State=%s",
                             service.binary, service.host, service.zone,
                             service.status, service.state)
        cpulse_log.critical("Nova Endpoint Check: OK")
    else:
        cpulse_log.critical("Nova service list error:%s", message)
        cpulse_log.critical("Nova Endpoint Check: FAIL")


def keystone_endpoint_check(keystone_instance):
    status, message, service_list = keystone_instance.keystone_service_list()
    if status == 200:
        for service in service_list:
            cpulse_log.debug("Service=%s enabled=%s", service.name,
                             service.enabled)
        cpulse_log.critical("Keystone Endpoint Check: OK")
    else:
        cpulse_log.critical("Keystone service list error:%s", message)
        cpulse_log.critical("Keystone Endpoint Check: FAIL")


def neutron_endpoint_check(neutron_instance):
    status, message, agent_list = neutron_instance.neutron_agent_list()
    if status == 200:
        for agent in agent_list:
            cpulse_log.debug("Agent=%s Host=%s Alive=%s admin_state_up=%s",
                             agent['binary'], agent['host'], agent['alive'],
                             agent['admin_state_up'])
        cpulse_log.critical("Neutron endpoint Check: OK")
    else:
        cpulse_log.debug("neutron agent list error:%s", message)
        cpulse_log.critical("Neutron endpoint Check: FAIL")


def glance_endpoint_check(glance_instance):
    status, message, image_list = glance_instance.glance_image_list()
    if status == 200:
        for image in image_list:
            cpulse_log.debug("Image=%s Status=%s", image.name, image.status)
        cpulse_log.critical("Glance endpoint Check: OK")
    else:
        cpulse_log.debug("Image List error:%s", message)
        cpulse_log.critical("Glance endpoint Check: FAIL")


def cinder_endpoint_check(cinder_instance):
    status, message, cinder_list = cinder_instance.cinder_list()
    if status == 200:
        cpulse_log.critical("Cinder endpoint Check: OK")
    else:
        cpulse_log.critical("Cinder list error:%s", message)
        cpulse_log.critical("Cinder endpoint Check: FAIL")


def health_check_start():
    """
    Function that triggers the health Check of
    various Openstack components
    """
    # Create the keystone client for all operations
    creds = cred.get_credentials()
    creds_nova = cred.get_nova_credentials_v2()
    # Create the clients for all components
    nova_instance = nova_api.NovaHealth(creds_nova)
    neutron_instance = neutron_api.NeutronHealth(creds)
    keystone_instance = keystone_api.KeystoneHealth(creds)
    glance_instance = glance_api.GlanceHealth(keystone_instance)
    cinder_instance = cinder_api.CinderHealth(creds_nova)
    # Check the health of various endpoints
    nova_endpoint_check(nova_instance)
    neutron_endpoint_check(neutron_instance)
    keystone_endpoint_check(keystone_instance)
    glance_endpoint_check(glance_instance)
    cinder_endpoint_check(cinder_instance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Health Check status check")
    parser.add_argument('-r', '--rc', dest='rc',
                        action='store',
                        help='source Openstack credentials from rc file',
                        metavar='<openrc_file>')
    parser.add_argument('-p', '--password', dest='pwd',
                        action='store',
                        help='Openstack password',
                        metavar='<password>')
    parser.add_argument('--noenv', dest='no_env',
                        default=False,
                        action='store_true',
                        help='do not read env variables')
    parser.add_argument('-d', '--debug', dest='debug',
                        default=False,
                        action='store_true',
                        help='debug level',
                        )
    (opts, args) = parser.parse_known_args()
    cred = credentials.Credentials(opts.rc, opts.pwd, opts.no_env)
    cpulse_log = logging.getLogger()
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s '
                                  '- %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    cpulse_log.addHandler(ch)
    ch.setFormatter(formatter)

    if opts.debug:
        cpulse_log.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    health_check_start()
