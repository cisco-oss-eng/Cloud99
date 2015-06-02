from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra
from ha_engine.ha_constants import HAConstants
from utils import utils
from utils.ansibleutils import AnsibleRunner
import time
import os
from monitors.plugins.openstack_api import credentials,nova_api

LOG = infra.ha_logging(__name__)

class VMDisruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def vm_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution
        infra.display_on_terminal(self, "Entering  VM Disruption plugin")

        table_name = "VM Disruption"
        infra.create_report_table(self, table_name)
        infra.add_table_headers(self, table_name,
                                ["VM", "IP", "TimeStamp",
                                 "Status of Disruption"])

        infra.display_on_terminal(self, "Entering  Process Disruption plugin")


        input_args_dict = self.get_input_arguments()
        print '========',input_args_dict
        node_name = input_args_dict.keys()[0]
        input_args = input_args_dict.get(node_name, None)
        host_config = infra.get_openstack_config()

        if input_args:
            print "Inpt " + str(input_args)
            role = input_args.get('role', None)

        print '*'*20
        print 'host_config ==',host_config
        print 'input_args ==',input_args
        print '*'*20 

        
        # nodes_to_be_disrupted = []
        for node in host_config:
            if role == host_config[node].get('role', None):
                jump_host = node   

        print jump_host
        nodes_to_be_disrupted = input_args.get('name')
        print nodes_to_be_disrupted

        node_reboot_command = "reboot"

        if self.sync:
            infra.display_on_terminal(self, "Waiting for notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification, Starting")

        openrc = host_config.get(jump_host, None).get('openrc', None)
        password = host_config.get(jump_host, None).get('password', None)

        print openrc
        ha_interval = self.get_ha_interval()
        # for i in range(1):
        while infra.is_execution_completed(self.finish_execution) is False:
           for node in nodes_to_be_disrupted:
                # node = nodes_to_be_disrupted[0]
                # ip = host_config.get(node, None).get('ip', None)
                # user = host_config.get(node, None).get('user', None)
                # password = host_config.get(node, None).get('password', None)
                ip = node
                # openrc = host_config.get(node, None).get('openrc', None)
                # password = host_config.get(node, None).get('password', None)
                infra.display_on_terminal(self, "IP: ", ip, " openrc: ",
                                          openrc)

                infra.display_on_terminal(self, "Executing ",
                                          node_reboot_command)


                # Using nova api performing the vm stop operation
                cred = credentials.Credentials(openrc, password,'no_env')

                try:
                    nova = nova_api.NovaHealth(cred.get_nova_credentials_v2())
                    ret = nova.nova_stop_server(ip)
                    time.sleep(ha_interval)
                    infra.display_on_terminal(self, "Rebooting ",ip)
                    nova.nova_start_server(ip)
                    error = []
                except Exception,error:
                    pass

                if error:
                    infra.display_on_terminal(self, "Error ", error,
                                              "color=red")

                infra.display_on_terminal(self, "waiting for ", ip, " to "
                                                                    "come "
                                                                    "online")
                if infra.wait_for_ping(ip, 240, 10):
                    infra.display_on_terminal(self, "Node ", ip,
                                              " is online", "color=green")

                infra.display_on_terminal(self, "Will sleep for interval ",
                                          str(ha_interval))
                #time.sleep(ha_interval)
                infra.add_table_rows(self, table_name, [[node,
                                                         ip,
                                                         utils.get_timestamp(),
                                                         HAConstants.OKGREEN +
                                                         'Rebooted' +
                                                         HAConstants.ENDC]])

        # bring it back to stable state
        infra.display_on_terminal(self, "Waiting for the node to become stable")
        if infra.wait_for_ping(ip, 240, 10):
            infra.display_on_terminal(self, "Node ", ip, " is in stable state",
                                      "color=green")
        infra.display_on_terminal(self, "Finishing Node Disruption")

    def set_expected_failures(self):
        pass

    def process_disruption(self, sync=None, finish_execution=None):
        pass
    def node_disruption(self, sync=None, finish_execution=None):
        pass

    def start_disruption(self, sync=None, finish_execution=None):
        pass

    def is_module_exeution_completed(self):
        return infra.is_execution_completed(finish_execution=
                                            self.finish_execution)

    def stop_disruption(self):
        pass

    def set_report(self):
        pass

    def display_report(self):
        pass

    def baremetal_disruption(self, sync=None, finish_execution=None):
        pass

