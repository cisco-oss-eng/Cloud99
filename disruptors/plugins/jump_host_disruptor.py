from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra
from ha_engine.ha_constants import HAConstants
from utils import utils
from utils.ansibleutils import AnsibleRunner
import time
import os
LOG = infra.ha_logging(__name__)

class JumpHostDisruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def jump_host_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution
        infra.display_on_terminal(self, "Entering Jump Host Disruption plugin")

        table_name = "Jump host Disruption"
        infra.create_report_table(self, table_name)
        infra.add_table_headers(self, table_name,
                                ["VM", "IP", "TimeStamp",
                                 "Status of Disruption"])

        infra.display_on_terminal(self, "Entering  Process Disruption plugin")


        input_args_dict = self.get_input_arguments()
        node_name = input_args_dict.keys()[0]
        input_args = input_args_dict.get(node_name, None)
        host_config = infra.get_openstack_config()

        print "*"*20
        print input_args_dict
        print "input_args ==>",input_args
        print "host_config ==>",host_config


        nodes_to_be_disrupted = input_args.get('name',[])
        
        if input_args:
            print "Inpt " + str(input_args)
            role = input_args.get('role', None)

        # jump_hosts = []
        for node in host_config:
            if role in host_config[node].get('role', None):
                jump_host = node
                # jump_hosts.append(node)

        print "###############",jump_host

        node_reboot_command = "reboot -f"

        if self.sync:
            infra.display_on_terminal(self, "Waiting for notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification, Starting")

        ha_interval = self.get_ha_interval()

        # jump host details
        jump_host_ip = host_config.get(node, None).get('ip', None)
        user = host_config.get(node,None).get('user',None)
        password = host_config.get(node,None).get('password',None)

        #TODO - if its more than one jump host

        # Write into txt file to pass via ansible playbook
        f = open('/tmp/remote_ips','w+')
        for ip in nodes_to_be_disrupted:
            f.write(ip+'\n')
        f.close()


        while infra.is_execution_completed(self.finish_execution) is False:
           # for node in nodes_to_be_disrupted:
                # node = nodes_to_be_disrupted[0]
                # ip = host_config.get(node, None).get('ip', None)
                # user = host_config.get(node, None).get('user', None)
                # password = host_config.get(node, None).get('password', None)
                ip = node
                # openrc = host_config.get(node, None).get('openrc', None)
                # password = host_config.get(node, None).get('password', None)
                infra.display_on_terminal(self, "Nodes to be disrupted: ", str(nodes_to_be_disrupted), " Jump host: ",
                                          jump_host_ip)

                infra.display_on_terminal(self, "Executing ",
                                          node_reboot_command)
                print "*"*50
                print "user :",user
                print "password :", password
                print "jump_host_ip :",jump_host_ip
                ret = AnsibleRunner(jump_host_ip,user,password).execute_on_remote()
                print ret
                # parse the output for report

                # node_list = os.walk('/tmp/hainfra').next()[1]
                # output_objs = eval(open('/tmp/hainfra/'+node+'/tmp/output','r').read())
                output_objs = eval(open('/tmp/hainfra/output','r').read())
                print output_objs

                for results in output_objs:
                    error = []
                    for (hostname, result) in results['contacted'].items():
                        if 'failed' in result:
                            print "%s >>> %s" % (hostname, result['msg'])
                            error = result['msg']
                    
                    if error:
                        infra.display_on_terminal(self, "Error ", error,
                                                  "color=red")

                    infra.display_on_terminal(self, "waiting for ", hostname, " to "
                                                                        "come "
                                                                        "online")
                    if infra.wait_for_ping(hostname, 240, 5):
                        infra.display_on_terminal(self, "Node ", hostname,
                                                  " is online", "color=green")

                    infra.display_on_terminal(self, "Will sleep for interval ",
                                              str(ha_interval))
                    #time.sleep(ha_interval)
                    if not error:
                        infra.add_table_rows(self, table_name, [[jump_host_ip,
                                                                 hostname,
                                                                 utils.get_timestamp(),
                                                                 HAConstants.OKGREEN +
                                                                 'Rebooted' +
                                                                 HAConstants.ENDC]])

                    else:

                        infra.add_table_rows(self, table_name, [[jump_host_ip,
                                                                 hostname,
                                                                 utils.get_timestamp(),
                                                                 HAConstants.FAIL +
                                                                 str(error)+
                                                                 HAConstants.ENDC]])

                    # bring it back to stable state
                    '''
                    infra.display_on_terminal(self, "Waiting for the node to become stable")
                    if infra.wait_for_ping(hostname, 240, 10):
                        infra.display_on_terminal(self, "Node ", hostname, " is in stable state",
                                                  "color=green")
                    '''
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

