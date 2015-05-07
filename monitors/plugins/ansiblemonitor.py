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
import utils.utils as utils

SERVICE_LIST = [
    {'service': 'neutron-server', 'role': 'controller'},
    {'service': 'glance-api', 'role': 'controller'},
    {'service': 'glance-registry', 'role': 'controller'}]


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
        failed_hosts = []

        ###################################################
        # First validation is to make sure connectivity to
        # all the hosts was ok.
        ###################################################
        if results['dark']:
            print "Host connectivity issues on %s " % results['dark'].keys()
            failed_hosts.append(results['dark'].keys())
            results['status'] = 'FAIL'

        ##################################################
        # Now look for status 'failed'
        ##################################################
        for node in results['contacted'].keys():
            if 'failed' in results['contacted'][node]:
                if results['contacted'][node]['failed'] is True:
                    print "Operation \'failed\' [%s]" % node
                    failed_hosts.append(node)
                    results['status'] = 'FAIL'

        #################################################
        # Check for the return code 'rc' for each host.
        #################################################
        for node in results['contacted'].keys():
            rc = results['contacted'][node].get('rc', None)
            if rc is not None and rc != 0:
                print "Operation \'return code\' %s on host %s" % \
                    (results['contacted'][node]['rc'], node)
                failed_hosts.append(node)
                results['status'] = 'FAIL'

        ##################################################
        # Additional checks. If passed is a list of key/value
        # pairs that should be matched.
        ##################################################
        if checks is None:
            print "No additional checks validated"
            return results, failed_hosts

        for check in checks:
            key = check.keys()[0]
            value = check.values()[0]
            for node in results['contacted'].keys():
                if key in results['contacted'][node].keys():
                    if results['contacted'][node][key] != value:
                        print "Check %s failed. Expected: [%s] found: [%s]" % \
                            (check, value, results['contacted'][node][key])
                        failed_hosts.append(node)
                        results['status'] = 'FAIL'

        return (results, failed_hosts)

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

        results, failed_hosts = self.validate_results(results)
        if results['status'] != 'PASS':
            print "ANSIBLE: [%s] operation failed [%s] [hosts: %s]" % \
                (module, complex_args, failed_hosts)

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

    def ansible_ssh_ping_check(self,
                               host_list,
                               remote_user):
        '''
        Basic ping and ssh check
        '''
        ansi_result = {}
        ansi_result['name'] = "ssh_ping_check"

        ansi_result['ansi_result'] = self.ansirunner.\
            ansible_perform_operation(host_list=host_list,
                                      remote_user=remote_user,
                                      module="ping")
        msg = ""
        if ansi_result['ansi_result']['status'] == 'PASS':
            msg = "Ssh & Ping Check:".ljust(40) + "PASS".ljust(10)
        else:
            msg = "SSh & Ping Check:".ljust(40) + "FAIL".ljust(10)

        infra.display_on_terminal(self, msg)

        return ansi_result

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

        msg = ""
        pmsg = "Process Check [%s]" % process_name
        if ansi_result['ansi_result']['status'] == 'PASS':
            msg = pmsg.ljust(40) + "PASS".ljust(10)
        else:
            msg = pmsg.ljust(40) + "FAIL".ljust(10)

        #print "RESULTS:::: ", ansi_result['ansi_result']
        #host0 = ansi_result['ansi_result']['contacted'][host_list[0]]

        infra.display_on_terminal(self, msg)

        return ansi_result

    def ansible_check_rabbitmq(self,
                               host_list,
                               remote_user):
        '''
        Check the RabbitMQ Status
        '''
        ansi_result = {}
        ansi_result['name'] = "rabbitmq_check"

        args = "rabbitmqctl status | grep listeners"
        ansi_result['ansi_result'] = self.ansirunner.\
            ansible_perform_operation(host_list=host_list,
                                      remote_user=remote_user,
                                      module="shell",
                                      module_args=args)
        msg = ""
        if ansi_result['ansi_result']['status'] == 'PASS':
            msg = "RabbitMQ Check:".ljust(40) + "PASS".ljust(10)
        else:
            msg = "RabbitMQ Check:".ljust(40) + "FAIL".ljust(10)

        infra.display_on_terminal(self, msg)

        return ansi_result

    def ansible_check_mariadb(self,
                              host_list,
                              remote_user):
        '''
        Check MariaDB status.
        '''
        ansi_result = {}
        ansi_result['name'] = "mariadb_check"
        args = r"mysql -u %s -p%s -e 'show databases;'| grep cinder" % \
            (self.mariadb_user, self.mariadb_password)
        ansi_result['ansi_result'] = self.ansirunner.\
            ansible_perform_operation(host_list=host_list,
                                      remote_user=remote_user,
                                      module="shell",
                                      module_args=args)
        msg = ""
        if ansi_result['ansi_result']['status'] == 'PASS':
            msg = "MariaDB Check:".ljust(40) + "PASS".ljust(10)
        else:
            msg = "MariaDB Check:".ljust(40) + "FAIL".ljust(10)

        infra.display_on_terminal(self, msg)

        return ansi_result

    def display_ansible_report(self,
                               hist_cnt=5):
        '''
        Display the Ansible Report.
        '''
        infra.create_report_table(self, "Ansible Monitoring Summary")
        infra.add_table_headers(self, "Ansible Monitoring Summary",
                                ["Timestamp",
                                 "SSH & Ping",
                                 "RabbitMQ",
                                 "MariaDB",
                                 "Process"])
        rows = []
        for ts_results in self.ansiresults:
            print "=========================================="
            singlerow = []
            process_check_status = 'PASS'
            for results in ts_results:
                #print "Result obj: ", results
                name = results.get('name', None)
                if name is None:
                    continue

                if name == "ts":
                    ts = results.get('ts', None)
                    singlerow.append(ts)
                if name == "process_check":
                    if results['ansi_result']['status'] == 'FAIL':
                        process_check_status = 'FAIL'
                if name == "ssh_ping_check":
                    singlerow.append(results['ansi_result']['status'])
                if name == "rabbitmq_check":
                    singlerow.append(results['ansi_result']['status'])
                if name == "mariadb_check":
                    singlerow.append(results['ansi_result']['status'])
            singlerow.append(process_check_status)

            rows.append(singlerow)

        infra.add_table_rows(self,
                             "Ansible Monitoring Summary",
                             rows)
        infra.display_infra_report()

    def start(self, sync=None, finish_execution=None, args=None):
        '''
        Required start method to implement for the class.
        '''
        # Parse user data and Initialize.
        data = self.get_input_arguments()
        print "User data: ", data
        self.frequency = data['ansible'].get('frequency', 5)
        self.max_hist_size = data['ansible'].get('max_hist', 25)

        # Get MariaDB Username/pass
        self.mariadb_user = None
        self.mariadb_password = None
        mariadb_info = data['ansible'].get('mariadb', None)
        if mariadb_info is not None:
            self.mariadb_user = data['ansible']['mariadb'].get('user', None)
            self.mariadb_password = data['ansible']['mariadb'].get('password',
                                                                   None)

        self.ansirunner = None
        setup_file = "../../configs/openstack_config.yaml"
        self.ansiresults = collections.deque(maxlen=self.max_hist_size)

        inventory = ConfigHelper(host_file=setup_file)
        print "parsed data: ", inventory.parsed_data

        host_list = inventory.get_host_list()
        host_ip_list = inventory.get_host_ip_list()
        control_ip_list = inventory.get_host_ip_list(role='controller')
        compute_ip_list = inventory.get_host_ip_list(role='compute')
        remote_user = inventory.get_host_username(host_list[0])
        print "Inventory: [all: %s], [control: %s] [compute: %s]" % \
            (host_ip_list, control_ip_list, compute_ip_list)
        print "Remote user: ", remote_user
        self.ansirunner = AnsibleRunner()

        cnt = 0
        while True:
            cnt += 1
            if cnt > 3:
                break
            ####################################################
            # Ansible Monitoring Loop.
            ####################################################
            ts_results = []
            ts = utils.get_monitor_timestamp()
            ts_results.append({'name': 'ts', 'ts': ts})
            msg = "=" * 50 + "\n" + "Timestamp: " + ts
            infra.display_on_terminal(self, msg)

            # Ping and SSH Check.
            host_ip_list = inventory.get_host_ip_list()
            ansi_results = self.ansible_ssh_ping_check(host_ip_list,
                                                       remote_user)
            ts_results.append(ansi_results)

            # Process check.
            for service in SERVICE_LIST:
                host_ip_list = inventory.get_host_ip_list(role=service['role'])
                ansi_results = self.ansible_check_process(host_ip_list,
                                                          remote_user,
                                                          service['service'])
                ts_results.append(ansi_results)

            # RabbitMQ Check.
            host_ip_list = inventory.get_host_ip_list(role='controller')
            ansi_results = self.ansible_check_rabbitmq(host_ip_list,
                                                       remote_user)
            ts_results.append(ansi_results)

            # MariaDB Check.
            ansi_results = self.ansible_check_mariadb(host_ip_list,
                                                      remote_user)
            ts_results.append(ansi_results)

            # Add the ts results to main result list.
            self.ansiresults.append(ts_results)

            time.sleep(self.frequency)

        self.display_ansible_report()



def main():
    # For test purposes only.
    print "Ansible Monitor should be called for HA Framework only."

if __name__ == '__main__':
    main()
