from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra
import time
LOG = infra.ha_logging(__name__)

class NodeDisruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def node_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution
        infra.display_on_terminal(self, "Entering  Node Disruption plugin")

        input_args_dict = self.get_input_arguments()
        node_name = input_args_dict.keys()[0]
        input_args = input_args_dict.get(node_name, None)
        host_config = infra.get_openstack_config()

        if input_args:
            print "Inpt " + str(input_args)
            role = input_args.get('role', None)


        nodes_to_be_disrupted = []
        for node in host_config:
            if role in host_config[node].get('role', None):
                infra.display_on_terminal(self, node, " will be disrupted ")
                nodes_to_be_disrupted.append(node)

        node_reboot_command = "reboot -f "

        if self.sync:
            infra.display_on_terminal(self, "Waiting for notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification, Starting")

        ha_interval = self.get_ha_interval()
        for i in range(1):
        #while infra.is_execution_completed(self.finish_execution) is False:
           # for node in nodes_to_be_disrupted:
                node = nodes_to_be_disrupted[0]
                ip = host_config.get(node, None).get('ip', None)
                user = host_config.get(node, None).get('user', None)
                password = host_config.get(node, None).get('password', None)
                infra.display_on_terminal(self, "IP: ", ip, " User: ",
                                          user, " Pwd: ", password)
                infra.display_on_terminal(self, "Executing ",
                                          node_reboot_command)
                code, out, error = infra.ssh_and_execute_command(ip, user,
                                                                 password,
                                                            node_reboot_command)
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

        # bring it back to stable state
        infra.display_on_terminal(self, "Waiting for the node to become stable")
        if infra.wait_for_ping(ip, 240, 10):
            infra.display_on_terminal("Node ", ip, " is in stable state",
                                      "color=green")

        infra.display_on_terminal(self, "Finishing Node Disruption")

    def process_disruption(self, sync=None, finish_execution=None):
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

