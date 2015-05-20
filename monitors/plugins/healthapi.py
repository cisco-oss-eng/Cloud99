from monitors.baseMonitor import BaseMonitor
import ha_engine.ha_infra as infra
import utils.utils
import time
import openstack_api.credentials
import openstack_api.nova_api
import openstack_api.neutron_api
import openstack_api.glance_api
import openstack_api.cinder_api
import openstack_api.keystone_api
import collections
import os
from ha_constants import HAConstants

LOG = infra.ha_logging(__name__)

class HealthAPI(BaseMonitor):
    # Create Table and add header
    finish_execution = None
    agents_downtime_dict = collections.OrderedDict()
    endpoint_downtime_dict = collections.OrderedDict()
    nagios_graph_file = "/tmp/ha_infra/healthapi.txt"

    def start(self, sync=None, finish_execution=None, mode="basic"):
        infra.display_on_terminal(self, 'Starting Endpoint Health Check')
        input_args = self.get_input_arguments()
        self.finish_execution = finish_execution

        if 'openrc_file' in input_args['openstack_api']:
            openrc = input_args['openstack_api']['openrc_file']
        else:
            openrc = None
        if 'password' in input_args['openstack_api']:
            
            password = input_args['openstack_api']['password']
        else:
            password = None
        
        if openrc and password:
            noenv = True
        else:
            noenv = False

        self.cred = openstack_api.credentials.Credentials(openrc, password,
                                                          noenv)
        self.frequency = input_args['openstack_api']['frequency']
        max_entries = input_args['openstack_api']['max_entries']
 
        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification from Runner")

        self.add_to_graph_file("starttime##"+utils.utils.get_timestamp
        (complete_timestamp=True))
        self.health_check_start()
        self.add_to_graph_file("endtime##"+utils.utils.get_timestamp
        (complete_timestamp=True))
        infra.display_on_terminal(self, "Finished Monitoring")

        # Generate downtime range of all the endpoints
        self.generate_downtime_table(self.endpoint_downtime_dict,
                                     "Endpoints Downtime")

        # Generate downtime range table for all the agents
        self.generate_downtime_table(self.agents_downtime_dict,
                                     "Agent Downtime")

        # Display the final report
        tables_list = ['Endpoints Downtime', 'Agent Downtime']

    def display_msg_on_term(self, msg, status, host_list=None):
        '''
        Generic function invoked by other check functions to print
        status.
        '''
        msg = msg.ljust(50)
        status_msg = status.ljust(10)
        msg = msg + status_msg

        if host_list is not None and len(host_list) > 0:
            msg = msg + str(host_list)
        if status == 'PASS':
            infra.display_on_terminal(self, msg, "color=green")
        else:
            infra.display_on_terminal(self, msg, "color=red")

    def health_check_start(self):
        creds = self.cred.get_credentials()
        creds_nova = self.cred.get_nova_credentials_v2()
        nova_instance = openstack_api.nova_api.NovaHealth(creds_nova)
        neutron_instance = openstack_api.neutron_api.NeutronHealth(creds)
        keystone_instance = openstack_api.keystone_api.KeystoneHealth(creds)
        glance_instance = \
            openstack_api.glance_api.GlanceHealth(keystone_instance)
        cinder_instance = openstack_api.cinder_api.CinderHealth(creds_nova)

        while infra.is_execution_completed(self.finish_execution) is False:
            self.ts, self.cts = utils.utils.get_timestamp(), \
                                   utils.utils.get_timestamp(
                                       complete_timestamp=True)

            self.nova_endpoint_check(nova_instance)
            self.neutron_endpoint_check(neutron_instance)
            self.keystone_endpoint_check(keystone_instance)
            self.glance_endpoint_check(glance_instance)
            self.cinder_endpoint_check(cinder_instance)

            # Check service status
            self.nova_endpoint_check(nova_instance,
                                     detail=True)
            self.neutron_endpoint_check(neutron_instance,
                                        detail=True)
            time.sleep(self.frequency)


    def nova_endpoint_check(self, nova_instance, detail=False):
        status, message, service_list = nova_instance.nova_service_list()
        if status == 200:
            if detail == False:
                self.display_msg_on_term("Nova Endpoint Check", "PASS")
                self.update_downtime_dict(self.endpoint_downtime_dict,
                                          'nova-api', 'All Hosts', 'OK')
            else:
                for service in service_list:
                    service_data = "Binary=%s   Host=%s  Status=%s  State=%s"\
                                   % (service.binary, service.host,
                                      service.status, service.state)
                    color = "color=green"
                    msg = "%s state" % service.binary
                    if service.state == 'down':
                        color = "color=red"
                        self.update_downtime_dict(self.agents_downtime_dict,
                                                  service.binary, service.host,
                                                  'FAIL')
                        self.display_msg_on_term(msg, "FAIL", [service.host])
                    else:
                        self.update_downtime_dict(self.agents_downtime_dict,
                                                  service.binary, service.host,
                                                  'OK')
                        self.display_msg_on_term(msg, "PASS", [service.host])
        else:
            
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'nova-api', 'All Hosts', 'FAIL')

            if detail == True:
                self.display_msg_on_term("nova-api state", "FAIL")
            else:
                self.display_msg_on_term("Nova Endpoint Check", "FAIL")
            
    def neutron_endpoint_check(self, neutron_instance, detail=False):
        status, message, agent_list = neutron_instance.neutron_agent_list()
        if status == 200:
            if detail == False:
                self.display_msg_on_term("Neutron Endpoint Check", "PASS")
                self.update_downtime_dict(self.endpoint_downtime_dict,
                                    'neutron-server', 'All Hosts', 'OK')
            else:
                for agent in agent_list:
                    state = "PASS"
                    agent_data = "Agent=%s Host=%s Alive=%s  Admin State=%s"\
                                 % (agent['binary'], agent['host'],
                                    agent['alive'], agent['admin_state_up'])
                    color = "color=green"
                    if agent['alive']:
                        agent['Status'] = 'OK'
                    else:
                        state = "FAIL"
                        agent['Status'] = 'FAIL'
                    if agent['admin_state_up']:
                        agent['State'] = 'OK'
                    else:
                        state = "FAIL"
                        agent['State'] = 'FAIL'

                    self.update_downtime_dict(self.agents_downtime_dict,
                                              agent['binary'], agent['host'],
                                              agent['Status'])
                    msg = "%s state" % agent['binary']
                    self.display_msg_on_term(msg, state, [agent['host']])
        else:
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'neutron-server', 'All Hosts', 'FAIL')
            if detail == True:
                self.display_msg_on_term("neutron-server state", "FAIL")
            else:
                self.display_msg_on_term("Neutron Endpoint Check" , "FAIL")

    def keystone_endpoint_check(self, keystone_instance):
        status, message, service_list = \
            keystone_instance.keystone_service_list()
        if status == 200:
            self.display_msg_on_term("Keystone Endpoint Check" , "PASS")
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'keystone', 'All Hosts', 'OK')
        else:
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'keystone', 'All Hosts', 'FAIL')
            self.display_msg_on_term("Keystone Endpoint Check", "FAIL")
    
    def glance_endpoint_check(self, glance_instance):
        status, message, image_list = glance_instance.glance_image_list()
        if status == 200:
            self.display_msg_on_term("Glance Endpoint Check", "PASS")
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'glance-api', 'All Hosts', 'OK')
        else:
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'glance-api', 'All Hosts', 'FAIL')
            self.display_msg_on_term("Glance Endpoint Check", "FAIL")
    
    def cinder_endpoint_check(self, cinder_instance):
        status, message, cinder_list = cinder_instance.cinder_list()
        if status == 200:
            self.display_msg_on_term("Cinder Endpoint Check", "PASS")
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'cinder-api', 'All Hosts', 'OK')
        else:
            self.update_downtime_dict(self.endpoint_downtime_dict,
                                      'cinder-api', 'All Hosts', 'FAIL')
            self.display_msg_on_term("Cinder Endpoint Check", "FAIL")
        
    def stop(self):
        infra.display_on_terminal(self, "Stopping the Keystone...")

    def set_report(self):
        self.ha_report.append(self.report)

    def get_report(self):
        infra.display_report(None)

    def notify(self, *args, **kwargs):
        infra.display_on_terminal(self, 'Args is  %s', str(args))
        for key, value in kwargs.iteritems():
            infra.display_on_terminal(self,
                                      'Got Notification with key %s, value %s'
                                      % (key, value))

    def generate_downtime_table(self, downtime_dict, table_name):

        host_agent_status_dict = collections.OrderedDict()
        col_pos_dict = {}
        all_agent_list = [agent for agent in downtime_dict]
        infra.create_report_table(self, table_name)
        headers = ["Host Names "] + all_agent_list
        infra.add_table_headers(self, table_name, headers)

        col_pos = 0
        for agent in downtime_dict:
            count = 0
            col_pos_dict[agent] = col_pos
            for agent_dict in downtime_dict[agent]:
                if agent_dict is None:
                    print "No agent."
                for host in agent_dict:
                    cur = None
                    prev = None
                    downtime_range_start = None
                    downtime_range_stop = None
                    downtime_range = set()
                    host_dict = agent_dict[host]
                    for ts, status in host_dict.items():
                        count += 1
                        cur = status

                        if (cur == 'FAIL' and prev == 'OK') or \
                                (cur == 'FAIL' and prev is None):
                            downtime_range_start = ts
                        if cur == 'FAIL' and prev == cur:
                            downtime_range_stop = ts
                        if cur == 'FAIL' and count == len(host_dict):
                            downtime_range_stop = ts
                        if cur == 'OK' and prev == 'FAIL' or\
                                (cur == 'FAIL' and count == len(host_dict)):
                            downtime_range_stop = ts
                            downtime_range.add(downtime_range_start + " to " +
                                               downtime_range_stop)
                        prev = cur

                    if not downtime_range:
                        all_down_range = HAConstants.OKGREEN + ":)" + \
                                         HAConstants.ENDC
                    else:
                        all_down_range = HAConstants.WARNING +\
                                         (", ".join(downtime_range)) +\
                                         HAConstants.ENDC

                    host_dict = {agent: all_down_range}
                    if host_agent_status_dict.get(host, None) is None:
                        host_agent_status_dict[host] = [host_dict]
                    else:
                        host_agent_status_dict.get(host, None).append(host_dict)
            col_pos += 1

        for host in host_agent_status_dict:
            row = [host]
            agents = ['-'] * len(all_agent_list)
            available_agents = set()
            for agent in host_agent_status_dict[host]:
                available_agents.add(agent.keys()[0])

            missing_agents = set()
            for agent_status in host_agent_status_dict[host]:
                missing_agents = set(all_agent_list).difference(available_agents)
                for agent_name, status in agent_status.items():
                    colpos = col_pos_dict.get(agent_name)
                    status = agent_status.get(agent_name, None)
                    agents[colpos] = status
            for missing_agent in missing_agents:
                colpos = col_pos_dict.get(missing_agent)
                na_status = 'NA'
                agents[colpos] = na_status

            infra.add_table_rows(self, table_name, [row + agents])

    def update_downtime_dict(self, downtime_dict, agent_name,
                             host_name, status):
        # adding to graph file
        # format control-1,Neutron Network List,2015-05-08 11:30:37,OK,4
        g_status = "CRITICAL" if status == "FAIL" else status
        self.add_to_graph_file(host_name+","+agent_name+
                               ","+self.cts+","+g_status+","+"")
        if downtime_dict.get(agent_name, None):
            agents_host_list = downtime_dict[agent_name]

            down_dict = [d for d in agents_host_list if host_name in d]
            if down_dict:
                down_dict[0].get(host_name)[self.ts] = status
            else:
                down_dict = collections.OrderedDict({self.ts: status})
                downtime_dict[agent_name].\
                    append({host_name: down_dict })
        else:
            down_dict = collections.OrderedDict({self.ts: status})
            downtime_dict[agent_name] = \
                [{host_name: down_dict}]

    def add_to_graph_file(self, msg):
        msg += "\n"
        if not os.path.isfile(self.nagios_graph_file):
            with open(self.nagios_graph_file, "w+") as f:
                f.write(msg)
        else:
            with open(self.nagios_graph_file, "a+") as f:
                f.write(msg)


""" 
if __name__ == "__main__":
    health_instance = HealthAPI()
    health_instance.start()
"""
