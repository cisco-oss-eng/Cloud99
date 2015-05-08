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

LOG = infra.ha_logging(__name__)


class HealthAPI(BaseMonitor):
    # Create Table and add header
    table_endpoint_check = "Health Status: Endpoint Check"
    table_service_check  = "Health Status: Service Status Check"
    finish_execution = None
    agents_downtime_dict = collections.OrderedDict()
    endpoint_downtime_dict = collections.OrderedDict()

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
        self.endpoint_results = collections.deque(maxlen=max_entries)
        self.service_results = collections.deque(maxlen=max_entries)
 
        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification from Runner")

        self.health_check_start()
        infra.display_on_terminal(self, "Finished Monitoring")


    def health_check_start(self):
        creds = self.cred.get_credentials()
        creds_nova = self.cred.get_nova_credentials_v2()
        nova_instance = openstack_api.nova_api.NovaHealth(creds_nova)
        neutron_instance = openstack_api.neutron_api.NeutronHealth(creds)
        keystone_instance = openstack_api.keystone_api.KeystoneHealth(creds)
        glance_instance = \
            openstack_api.glance_api.GlanceHealth(keystone_instance)
        cinder_instance = openstack_api.cinder_api.CinderHealth(creds_nova)

        #for i in range(2):
        while infra.is_execution_completed(self.finish_execution) is False:
            ep_results = {}
            svc_results = []

            self.ts = utils.utils.get_monitor_timestamp()
            ep_results['timestamp'] = self.ts
            self.nova_endpoint_check(nova_instance, ep_results)
            self.neutron_endpoint_check(neutron_instance , ep_results)
            self.keystone_endpoint_check(keystone_instance, ep_results)
            self.glance_endpoint_check(glance_instance, ep_results)
            self.cinder_endpoint_check(cinder_instance, ep_results)

            # Check service status
            self.nova_endpoint_check(nova_instance,
                                     svc_results, detail=True)
            self.neutron_endpoint_check(neutron_instance,
                                        svc_results, detail=True)
            time.sleep(self.frequency)
            self.endpoint_results.append(ep_results)

            self.service_results.append(svc_results)

        self.health_display_report()

        # Generate downtime range of all the endpoints

        # Generate downtime range table for all the agents
        self.generate_downtime_table(self.agents_downtime_dict,
                                     "Agent Downtime")


    
    def health_display_report(self):
        infra.create_report_table(self, self.table_endpoint_check)
        infra.add_table_headers(self, self.table_endpoint_check,
                                ["TimeStamp", "Nova", "Neutron",
                                 "Keystone", "Glance", "Cinder"])
        infra.create_report_table(self, self.table_service_check)
        infra.add_table_headers(self, self.table_service_check,
                                ["TimeStamp", "Service", "Host",
                                 "Status", "State"])
        for endpoint in self.endpoint_results:
            infra.add_table_rows(self, self.table_endpoint_check,
                                 [
                                    [endpoint['timestamp'], endpoint['nova'],
                                   endpoint['neutron'], endpoint['keystone'],
                                            endpoint['glance'], endpoint['cinder']]])
        """
        for service in self.service_results:
            infra.add_table_rows(self, self.table_service_check,
                                 [
                                    [service['timestamp'], service['service'],
                                     service['host'], service['Status'],
                                     service['State']]])
        """
        infra.display_infra_report()
    

    def nova_endpoint_check(self, nova_instance, results, detail=False):
        status, message, service_list = nova_instance.nova_service_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Nova Endpoint Check: OK",
                                          "color=green")
                results['nova'] = 'OK'
            else:
                for service in service_list:
                    service_dict = {}
                    service_data = "Binary=%s   Host=%s   Status=%s   State=%s"\
                                   % (service.binary, service.host,
                                      service.status, service.state)
                    color = "color=green"
                    service_dict['ts'] = self.ts
                    service_dict['service'] = service.binary
                    service_dict['host'] = service.host
                    service_dict['Status'] = service.status
                    service_dict['State'] = service.state
                    if service.state == 'down':
                        color = "color=red"
                        self.update_downtime_dict(self.agents_downtime_dict,
                                                  service.binary, service.host,
                                                  'FAIL')
                    else:
                        self.update_downtime_dict(self.agents_downtime_dict,
                                                  service.binary, service.host,
                                                  'OK')
                    infra.display_on_terminal(self, service_data, color)
                    results.append(service_dict)
        else:
            infra.display_on_terminal(self, "Nova Endpoint Check: FAILED",
                                      "color=red")

            if detail == True:
                service_dict = {}
                service_dict['ts'] = self.ts
                service_dict['service'] ='nova-api'
                service_dict['host'] = 'NA'
                service_dict['Status'] = 'NA'
                service_dict['State'] = 'NA'
                results.append(service_dict)
            else:
                results['nova'] = 'FAIL'
            
        
    def neutron_endpoint_check(self, neutron_instance, results, detail=False):
        status, message, agent_list = neutron_instance.neutron_agent_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Neutron Endpoint Check: OK",
                                          "color=green")
                results['neutron'] = 'OK'
            else:
                for agent in agent_list:
                    agent_dict = {}
                    agent_data = "Agent=%s Host=%s Alive=%s  Admin State=%s"\
                                 % (agent['binary'], agent['host'],
                                    agent['alive'], agent['admin_state_up'])
                    color= "color=green"
                    agent_dict['ts'] = self.ts
                    agent_dict['service'] = agent['binary']
                    agent_dict['host'] = agent['host']
                    if agent['alive']:
                        agent_dict['Status'] = 'OK'
                    else:
                        color="color=red"
                        agent_dict['Status'] = 'FAIL'
                    if agent['admin_state_up']:
                        agent_dict['State'] = 'OK'
                    else:
                        color="color=red"
                        agent_dict['State'] = 'FAIL'

                    self.update_downtime_dict(self.agents_downtime_dict,
                                              agent['binary'], agent['host'],
                                              agent_dict['Status'])
                    infra.display_on_terminal(self, agent_data, color)
                    results.append(agent_dict)
        else:
            if detail == True:
                agent_dict = {}
                agent_dict['ts'] = self.ts
                agent_dict['Service'] = 'neutron-server'
                agent_dict['host'] = 'NA'
                agent_dict['Status'] = 'NA'
                agent_dict['State'] = 'NA'
                results.append(agent_dict)
            else:
                results['neutron'] = 'FAIL'
            infra.display_on_terminal(self, "Neutron Endpoint Check: FAIL",
                                      "color=red")

    
    def keystone_endpoint_check(self, keystone_instance, results):
        status, message, service_list = \
            keystone_instance.keystone_service_list()
        if status == 200:
            infra.display_on_terminal(self, "Keystone Endpoint Check: OK",
                                      "color=green")
            results['keystone'] = 'OK'
        else:
            infra.display_on_terminal(self, "Keystone Endpoint Check: FAIL",
                                      "color=red")
            results['keystone'] = 'FAIL'
    
    def glance_endpoint_check(self, glance_instance, results):
        status, message, image_list = glance_instance.glance_image_list()
        if status == 200:
            infra.display_on_terminal(self, "Glance endpoint Check: OK",
                                      "color=green")
            results['glance'] = 'OK'
        else:
            infra.display_on_terminal(self, "Glance endpoint Check: FAILED",
                                      "color=red")
            results['glance'] = 'FAIL'
    
    def cinder_endpoint_check(self, cinder_instance, results):
        status, message, cinder_list = cinder_instance.cinder_list()
        if status == 200:
            infra.display_on_terminal(self, "Cinder endpoint Check : OK",
                                      "color=green")
            results['cinder'] = 'OK'
        else:
            infra.display_on_terminal(self, "Cinder endpoint Check: FAILED",
                                      "color=red")
            results['cinder'] = 'FAIL'
        
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
                        if cur == 'OK' and prev == 'FAIL' or\
                                (cur == 'FAIL' and count == len(host_dict)):
                            downtime_range.add(downtime_range_start + " to " +
                                               downtime_range_stop)
                        prev = cur

                    if not downtime_range:
                        all_down_range = ":) "
                    else:
                        all_down_range = ", ".join(downtime_range)

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

        infra.display_infra_report()

    def update_downtime_dict(self, agents_downtime_dict, agent_name,
                             host_name, status):

        if agents_downtime_dict.get(agent_name, None):
            agents_host_list = agents_downtime_dict[agent_name]

            downtime_dict = [d for d in agents_host_list if host_name in d]
            if downtime_dict:
                downtime_dict[0].get(host_name)[self.ts] = status
            else:
                downtime_dict = collections.OrderedDict({self.ts: status})
                agents_downtime_dict[agent_name].\
                    append({host_name:downtime_dict })
        else:
            downtime_dict = collections.OrderedDict({self.ts: status})
            agents_downtime_dict[agent_name] = \
                [{host_name: downtime_dict}]

""" 
if __name__ == "__main__":
    health_instance = HealthAPI()
    health_instance.start()
"""
