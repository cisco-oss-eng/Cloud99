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
        self.cred = openstack_api.credentials.Credentials(openrc, password, noenv)
        self.frequency = input_args['openstack_api']['frequency']
        max_entries = input_args['openstack_api']['max_entries']
        self.endpoint_results = collections.deque(maxlen=max_entries)
        self.service_results = collections.deque(maxlen=max_entries)
 

        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)
            infra.display_on_terminal(self, "Received notification from Runner")
        self.health_check_start()


    def health_check_start(self):
        creds = self.cred.get_credentials()
        creds_nova = self.cred.get_nova_credentials_v2()
        nova_instance = openstack_api.nova_api.NovaHealth(creds_nova)
        neutron_instance = openstack_api.neutron_api.NeutronHealth(creds)
        keystone_instance = openstack_api.keystone_api.KeystoneHealth(creds)
        glance_instance = \
            openstack_api.glance_api.GlanceHealth(keystone_instance)
        cinder_instance = openstack_api.cinder_api.CinderHealth(creds_nova)

        for x in range(5):
        #while infra.is_execution_completed(self.finish_execution) is False:
            ep_results = {}
            svc_results = {}
            
            ep_results['timestamp'] = utils.utils.get_monitor_timestamp()
            svc_results['timestamp'] = utils.utils.get_monitor_timestamp()
            self.nova_endpoint_check(nova_instance, ep_results)
            self.neutron_endpoint_check(neutron_instance , ep_results)
            self.keystone_endpoint_check(keystone_instance, ep_results)
            self.glance_endpoint_check(glance_instance, ep_results)
            self.cinder_endpoint_check(cinder_instance, ep_results)
            # Check service status
            self.nova_endpoint_check(nova_instance, svc_results, detail=True)
            self.neutron_endpoint_check(neutron_instance, svc_results, detail=True)
            time.sleep(self.frequency)
            self.endpoint_results.append(ep_results)
            self.service_results.append(svc_results)

        self.health_display_report()
    
    def health_display_report(self):
        infra.create_report_table(self, self.table_endpoint_check)
        infra.add_table_headers(self, self.table_endpoint_check,
                                ["TimeStamp", "Nova", "Neutron", "Keystone", "Glance", "Cinder"])
        infra.create_report_table(self, self.table_service_check)
        infra.add_table_headers(self, self.table_service_check,
                                ["TimeStamp", "Service", "Host", "Status", "State"])
        for endpoint in self.endpoint_results:
            infra.add_table_rows(self, self.table_endpoint_check,
                                 [
                                    [endpoint['timestamp'], endpoint['nova'],
                                   endpoint['neutron'], endpoint['keystone'],
                                            endpoint['glance'], endpoint['cinder']]])
        for service in self.service_results:
            infra.add_table_rows(self, self.table_service_check,
                                 [
                                    [service['timestamp'], service['service'],
                                     service['host'], service['Status'],
                                     service['State']]])
        infra.display_infra_report()
    

    def nova_endpoint_check(self, nova_instance, results, detail=False):
        status, message, service_list = nova_instance.nova_service_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Nova Endpoint Check: OK")
                results['nova'] = 'OK'
            else:
                for service in service_list:
                    service_data = "Binary=%s   Host=%s   Status=%s   State=%s" %(service.binary, service.host,
                                                                                  service.status, service.state)
                    infra.display_on_terminal(self, service_data)
                    results['service'] = service.binary
                    results['host'] = service.host
                    results['Status'] = service.status
                    results['State'] = service.state
        else:
            infra.display_on_terminal(self, "Nova Endpoint Check: FAILED")
            if detail == True:
                results['service'] ='NA'
                results['host'] = 'NA'
                results['Status'] = NA
                results['State'] = NA
            else:
                results['nova'] = 'FAIL'
            
        
    def neutron_endpoint_check(self, neutron_instance, results, detail=False):
        status, message, agent_list = neutron_instance.neutron_agent_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Neutron Endpoint Check: OK")
                results['neutron'] = 'OK'
            else:
                for agent in agent_list:
                    agent_data = "Agent=%s   Host=%s   Alive=%s   Admin State=%s" % (agent['binary'], agent['host'],
                                                                                     agent['alive'], agent['admin_state_up'])
                    infra.display_on_terminal(self, agent_data)
                    results['service'] = agent['binary']
                    results['host'] = agent['host']
                    if agent['alive']:
                        results['Status'] = 'UP'
                    else:
                        results['Status'] = 'DOWN'
                    if agent['admin_state_up']:
                        results['State'] = 'UP'
                    else:
                        results['State'] = 'DOWN'
        else:
            if detail == True:
                results['Service'] = 'NA'
                results['host'] = 'NA'
                results['Status'] = 'NA'
                results['State'] = 'NA'
            else:
                results['neutron'] = 'FAIL'
            infra.display_on_terminal(self, "Neutron Endpoint Check: FAIL")

    
    def keystone_endpoint_check(self, keystone_instance, results):
        status, message, service_list = \
            keystone_instance.keystone_service_list()
        if status == 200:
            infra.display_on_terminal(self, "Keystone Endpoint Check: OK")
            results['keystone'] = 'OK'
        else:
            infra.display_on_terminal(self, "Keystone Endpoint Check: FAIL")
            results['keystone'] = 'FAIL'
    
    def glance_endpoint_check(self, glance_instance, results):
        status, message, image_list = glance_instance.glance_image_list()
        if status == 200:
            infra.display_on_terminal(self, "Glance endpoint Check: OK")
            results['glance'] = 'OK'
        else:
            infra.display_on_terminal(self, "Glance endpoint Check: FAILED")
            results['glance'] = 'FAIL'
    
    def cinder_endpoint_check(self, cinder_instance, results):
        status, message, cinder_list = cinder_instance.cinder_list()
        if status == 200:
            infra.display_on_terminal(self, "Cinder endpoint Check : OK")
            results['cinder'] = 'OK'
        else:
            infra.display_on_terminal(self, "Cinder endpoint Check: FAILED")
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
            
""" 
if __name__ == "__main__":
    health_instance = HealthAPI()
    health_instance.start()
"""
