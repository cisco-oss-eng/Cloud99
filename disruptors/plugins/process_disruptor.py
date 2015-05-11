from disruptors.baseDisruptor import BaseDisruptor
from ha_constants import HAConstants
import ha_engine.ha_infra as infra
import time

LOG = infra.ha_logging(__name__)


class ProcessDisruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None
    expected_failures = []

    def process_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution

        table_name = "Process Disruption"
        infra.create_report_table(self, table_name)
        infra.add_table_headers(self, table_name,
                                ["Host", "Process", "Status of Disruption"])

        infra.display_on_terminal(self, "Entering  Process Disruption plugin")

        input_args_dict = self.get_input_arguments()
        node_name = input_args_dict.keys()[0]
        input_args = input_args_dict.get(node_name, None)
        host_config = infra.get_openstack_config()

        if input_args:
            print "Inpt " + str(input_args)
            process_name = input_args.get('process_name', None)
            role = input_args.get('role', None)
            type = input_args.get('type', None)

        infra.display_on_terminal(self, "Process ", process_name,
                                  " will be disrupted")

        nodes_to_be_disrupted = []
        for node in host_config:
            if 'controller' in host_config[node].get('role', None):
                infra.display_on_terminal(self, node, " will be disrupted ")
                nodes_to_be_disrupted.append(node)
                self.expected_failures.append(node + "::" + process_name)

        self.set_expected_failures(self.expected_failures)
        rhel_stop_command = "systemctl stop " + process_name
        rhel_start_command = "systemctl start " + process_name

        if sync:
            infra.display_on_terminal(self, "Waiting for notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification, Starting")

        ha_interval = self.get_ha_interval()
        while infra.is_execution_completed(self.finish_execution) is False:
            for node in nodes_to_be_disrupted:
                ip = host_config.get(node, None).get('ip', None)
                user = host_config.get(node, None).get('user', None)
                password = host_config.get(node, None).get('password', None)
                infra.display_on_terminal(self, "IP: ", ip, " User: ",
                                          user, " Pwd: ", password)
                infra.display_on_terminal(self, "Stopping ", process_name)
                infra.display_on_terminal(self, "Executing ", rhel_stop_command)
                code, out, error = infra.ssh_and_execute_command(ip, user,
                                                                 password,
                                                            rhel_stop_command)

                infra.display_on_terminal(self, "Sleeping for interval ",
                                      str(ha_interval), " seconds")
                time.sleep(ha_interval)
                infra.display_on_terminal(self, "Starting ", process_name)
                infra.display_on_terminal(self, "Executing ", rhel_start_command)
                code, out, error = infra.ssh_and_execute_command(ip, user,
                                                            password,
                                                         rhel_start_command)
                time.sleep(ha_interval)
                infra.add_table_rows(self, table_name,
                                     [[node, process_name,
                                       HAConstants.OKGREEN +
                                       'PASS' + HAConstants.ENDC]])

        # bring it back to stable state
        infra.display_on_terminal(self, "Bringing the process  to stable state")
        infra.display_on_terminal(self, "Executing ", rhel_start_command)
        code, out, error = infra.ssh_and_execute_command(ip, user, password,
                                                         rhel_start_command)

        infra.display_on_terminal(self, "Finishing Process Disruption")

    def set_expected_failures(self, expected_failures):
        self.expected_failures = expected_failures

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



