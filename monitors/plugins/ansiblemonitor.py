#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime
import yaml
import collections
import ansible.runner
from monitors.baseMonitor import BaseMonitor
import ha_engine.ha_infra as infra

SERVICE_LIST = [
    {'service': 'neutron_server', 'role': 'controller'},
    {'service': 'glance-api', 'role': 'controller'},
    {'service': 'glance-registry', 'role': 'controller'},
    {'service': 'foobar', 'role': 'controller'}]


def get_absolute_path_for_file(path, file_name, splitdir=None):
    """
    Return the filename in absolute path for any file
    passed as relative path.
    """
    base = os.path.basename(path)
    if splitdir is not None:
        splitdir = splitdir + "/" + base
    else:
        splitdir = base

    if os.path.isabs(path):
        abs_file_path = os.path.join(path.split(splitdir)[0],
                                     file_name)
    else:
        abs_file = os.path.abspath(path)
        abs_file_path = os.path.join(abs_file.split(splitdir)[0],
                                     file_name)

    return abs_file_path


def create_parsed_yaml(yaml_file):
    """
    Create a parsed yaml dictionalry from the yaml file.
    """
    try:
        fp = open(yaml_file)
    except IOError as ioerr:
        print "Failed to open file %s [%s]" % (yaml_file, ioerr)
        raise IOError(ioerr)

    try:
        parsed = yaml.load(fp)
    except yaml.error.YAMLError as perr:
        print "Failed to parse %s [%s]" % (yaml_file, perr)
        return None

    fp.close()
    return parsed


class ConfigHelper(object):
    '''
    ConfigHelper to parse the user host setup file.
    '''
    def __init__(self, host_file=None):
        '''
        Initialize ConfigHelper.
        '''
        if host_file is None:
            print "Host file not passed. exit"
            sys.exit(0)

        self.host_file = get_absolute_path_for_file(__file__,
                                                    host_file)
        if not os.path.exists(self.host_file):
            print "%s file does not exist" % self.host_file
            return

        self.parsed_data = create_parsed_yaml(self.host_file)

        print "Host Inventory initialized"

    def get_host_list(self):
        '''
        Get the list of hosts.
        '''
        host_list = []

        host_list = self.parsed_data.keys()

        return host_list

    def get_host_ip_list(self, role=None):
        '''
        Get the list of host ip addresses
        '''
        host_ip_list = []
        for host in self.parsed_data.keys():
            hrole = self.parsed_data[host].get('role', None)
            if role is not None and role != hrole:
                continue
            ip = self.parsed_data[host].get('ip', None)
            host_ip_list.append(ip)

        return host_ip_list

    def get_host_username(self, hostname):
        '''
        Get the username for the host.
        '''
        host = self.parsed_data.get(hostname, None)
        if host is None:
            print "host with name %s not found" % hostname
            return None

        return host.get('user', None)


class AnsibleRunner(object):
    '''
    AnsibleRunner Wrapper Class
    '''
    def __init__(self,
                 host_list=None,
                 remote_user=None,
                 sudo=False):
        '''
        AnsibleRunner init.
        '''
        self.host_list = host_list
        self.sudo = sudo

    def validate_host_parameters(self, host_list, remote_user):
        '''
        Set the hostlist and remote user .
        '''
        if host_list is None:
            host_list = self.host_list

        if remote_user is None:
            remote_user = self.remote_user

        if host_list is None or remote_user is None:
            print "Host list [%s], remote user [%s] are required" % \
                  (host_list, remote_user)
            self.log.error("Host list [%s], remote_user [%s] are required",
                           host_list, remote_user)
            return (None, None)

        return (host_list, remote_user)

    def validate_results(self, results, checks=None):
        '''
        Valdiate results from the Anisble Run.
        '''
        results['status'] = 'PASS'

        ###################################################
        # First validation is to make sure connectivity to
        # all the hosts was ok.
        ###################################################
        if results['dark']:
            print "Host connectivity issues on %s " % results['dark'].keys()
            results['status'] = 'FAIL'

        ##################################################
        # Now look for status 'failed'
        ##################################################
        for node in results['contacted'].keys():
            if 'failed' in results['contacted'][node]:
                if results['contacted'][node]['failed'] is True:
                    print "Operation \'failed\' [%s]" % node
                    results['status'] = 'FAIL'

        ##################################################
        # Additional checks. If passed is a list of key/value
        # pairs that should be matched.
        ##################################################
        if checks is None:
            print "No additional checks validated"
            return results

        for check in checks:
            key = check.keys()[0]
            value = check.values()[0]
            for node in results['contacted'].keys():
                if key in results['contacted'][node].keys():
                    if results['contacted'][node][key] != value:
                        print "Check %s failed. Expected: [%s] found: [%s]" % \
                            (check, value, results['contacted'][node][key])
                        results['status'] = 'FAIL'
        return results

    def ansible_perform_operation(self,
                                  host_list=None,
                                  remote_user=None,
                                  module=None,
                                  complex_args=None,
                                  module_args='',
                                  environment=None,
                                  check=False,
                                  forks=2):
        '''
        Perform any ansible operation.
        '''
        (host_list, remote_user) = \
            self.validate_host_parameters(host_list, remote_user)
        if (host_list, remote_user) is (None, None):
            return None

        if module is None:
            print "ANSIBLE Perform operation: No module specified"
            return None

        runner = ansible.runner.Runner(
            module_name=module,
            host_list=host_list,
            remote_user=remote_user,
            module_args=module_args,
            complex_args=complex_args,
            environment=environment,
            check=check,
            forks=forks)

        results = runner.run()

        results = self.validate_results(results)
        if results['status'] != 'PASS':
            print "ANSIBLE: [%s] operation failed [%s]" % \
                (module, complex_args)

        return results

    def ansible_execute_command(self, host_list=None, remote_user=None,
                                args=None, complex_args=None, forks=2):
        '''
        Execute a command on remote host using Ansible 'command'
        module
        '''

        (host_list, remote_user) = \
            self.validate_host_parameters(host_list, remote_user)
        if (host_list, remote_user) is (None, None):
            return None

        if args is None or len(args) == 0:
            print "Invalid command [%s]" % args
            return None

        cmd = " ".join(args)

        runner = ansible.runner.Runner(
            module_name="command",
            host_list=host_list,
            remote_user=remote_user,
            module_args=cmd,
            complex_args=complex_args,
            forks=forks)

        results = runner.run()

        results = self.validate_results(results, checks=[{'stderr': ''}])
        if results['status'] != 'PASS':
            print "Execute command %s failed" % cmd

        return results


class AnsibleMonitor(BaseMonitor):
    '''
    Anisble Monitor.
    '''
    def get_monitor_timestamp(self):
        '''
        Return the timestamp that will be added to the
        results.
        '''
        dt = datetime.datetime.now()
        timestamp = "%s:%s:%s-%s/%s/%s" % (dt.second, dt.minute, dt.hour,
                                           dt.month, dt.day, dt.year)

        return timestamp

    def ansible_check_process(self,
                              host_list, remote_user, process_name):
        '''
        Check the process status
        '''
        ansi_result = {}
        ansi_result['name'] = "process_check"
        ansi_result['process'] = process_name

        args = "ps -ef | grep %s | grep -v grep" % process_name
        ansi_result['ansi_result'] = self.ansirunner.\
            ansible_perform_operation(host_list=host_list,
                                      remote_user=remote_user,
                                      module="shell",
                                      module_args=args)

        #print "RESULTS:::: ", ansi_result['ansi_result']
        host0 = ansi_result['ansi_result']['contacted'][host_list[0]]

        infra.display_on_terminal(self, host0['stdout'])

        return ansi_result

    def start(self, sync=None, finish_execution=None, args=None):
        '''
        Required start method to implement for the class.
        '''
        # Initialize and Parse user input..
        self.ansirunner = None
        self.ansiresults = collections.deque(maxlen=5)
        setup_file = "../../configs/openstack_config.yaml"
        inventory = ConfigHelper(host_file=setup_file)

        print "parsed data: ", inventory.parsed_data
        print "host list: ", inventory.get_host_list()

        data = self.get_input_arguments()
        print "User data: ", data
        print "freq: ", data[0]['ansible']['frequency']
        self.frequency = data[0]['ansible'].get('frequency', 5)


        host_list = inventory.get_host_list()
        host_ip_list = inventory.get_host_ip_list()
        control_ip_list = inventory.get_host_ip_list(role='controller')
        compute_ip_list = inventory.get_host_ip_list(role='compute')
        remote_user = inventory.get_host_username(host_list[0])
        print "[all: %s], [control: %s] [compute: %s]" % \
            (host_ip_list, control_ip_list, compute_ip_list)
        print "Remote user: ", remote_user
        self.ansirunner = AnsibleRunner()

        while True:
            ####################################################
            # Ansible Monitoring Loop.
            ####################################################
            ts_results = []
            ts = self.get_monitor_timestamp()
            ts_results.append({'ts': ts})

            for service in SERVICE_LIST:
                host_ip_list = inventory.get_host_ip_list(role=service['role'])
                ansi_results = self.ansible_check_process(host_ip_list,
                                                          remote_user,
                                                          service['service'])
            ts_results.append(ansi_results)
            infra.display_on_terminal(self,
                                      "Ansible Module: test")

            # Add the ts results to main result list.
            self.ansiresults.append(ts_results)

            time.sleep(self.frequency)



def main():
    # For test purposes only.
    print "Ansible Monitor should be called for HA Framework only."

if __name__ == '__main__':
    main()
