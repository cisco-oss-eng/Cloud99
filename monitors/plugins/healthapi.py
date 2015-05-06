from monitors.baseMonitor import BaseMonitor
import ha_engine.ha_infra as infra
import time
import openstack_api.credentials
import openstack_api.nova_api
import openstack_api.neutron_api
import openstack_api.glance_api
import openstack_api.cinder_api
import openstack_api.keystone_api

LOG = infra.ha_logging(__name__)


class HealthAPI(BaseMonitor):
    # Create Table and add header
    table_endpoint_check = "Health Status: Endpoint Check"
    finish_execution = None

    def start(self, sync=None, finish_execution=None, mode="basic"):
        infra.display_on_terminal(self, 'Starting Endpoint Health Check')
        input_args = self.get_input_arguments()
        self.finish_execution = finish_execution
        if 'openrc_file' in input_args[0]['openstack_api']:
            openrc = input_args[0]['openstack_api']['openrc_file']
        else:
            openrc = None
        if 'password' in input_args[0]['openstack_api']:
            password = input_args[0]['openstack_api']['password']
        else:
            password = None
        
        if openrc and password:
            noenv = True
        else:
            noenv = False
        cred = openstack_api.credentials.Credentials(openrc, password, noenv)

        infra.create_report_table(self, self.table_endpoint_check)
        infra.add_table_headers(self, self.table_endpoint_check,
                                ["Endpoint", "Status"])

        if sync:
            infra.display_on_terminal(self, "Waiting for Runner Notification")
            infra.wait_for_notification(sync)

        infra.display_on_terminal(self, "Received notification from Runner")
        self.health_check_start(cred)


    def health_check_start(self, cred):
        creds = cred.get_credentials()
        creds_nova = cred.get_nova_credentials_v2()
        nova_instance = openstack_api.nova_api.NovaHealth(creds_nova)
        neutron_instance = openstack_api.neutron_api.NeutronHealth(creds)
        keystone_instance = openstack_api.keystone_api.KeystoneHealth(creds)
        glance_instance = \
            openstack_api.glance_api.GlanceHealth(keystone_instance)
        cinder_instance = openstack_api.cinder_api.CinderHealth(creds_nova)

        #while True:
        while not self.finish_execution:
            self.nova_endpoint_check(nova_instance)
            self.neutron_endpoint_check(neutron_instance)
            self.keystone_endpoint_check(keystone_instance)
            self.glance_endpoint_check(glance_instance)
            self.cinder_endpoint_check(cinder_instance)
            # Check service status
            self.nova_endpoint_check(nova_instance, detail=True)
            self.neutron_endpoint_check(neutron_instance, detail=True)
            time.sleep(2)

        infra.display_infra_report()

    def nova_endpoint_check(self, nova_instance, detail=False):
        status, message, service_list = nova_instance.nova_service_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Nova Endpoint Check: OK")
            else:
                for service in service_list:
                    service_data = "Binary=%s   Host=%s   Status=%s   State=%s" %(service.binary, service.host,
                                                                                  service.status, service.state)
                    infra.display_on_terminal(self, service_data)
            infra.add_table_rows(self, self.table_endpoint_check, [["Nova ", "OK"]])
        else:
            infra.display_on_terminal(self, "Nova Endpoint Check: FAILED")
            infra.add_table_rows(self, self.table_endpoint_check, [["Nova ", "FAIL"]])
        
    def neutron_endpoint_check(self, neutron_instance, detail=False):
        status, message, agent_list = neutron_instance.neutron_agent_list()
        if status == 200:
            if detail == False:
                infra.display_on_terminal(self, "Neutron Endpoint Check: OK")
            else:
                for agent in agent_list:
                    agent_data = "Agent=%s   Host=%s   Alive=%s   Admin State=%s" % (agent['binary'], agent['host'],
                                                                                     agent['alive'], agent['admin_state_up'])
                    infra.display_on_terminal(self, agent_data)
                
            infra.add_table_rows(self, self.table_endpoint_check, [["Neutron ", "OK"]])
        else:
            infra.display_on_terminal(self, "Neutron Endpoint Check: FAIL")
            infra.add_table_rows(self, self.table_endpoint_check, [["Neutron ", "FAIL"]])
    
    def keystone_endpoint_check(self, keystone_instance):
        status, message, service_list = \
            keystone_instance.keystone_service_list()
        if status == 200:
            infra.display_on_terminal(self, "Keystone Endpoint Check: OK")
            infra.add_table_rows(self, self.table_endpoint_check, [["Keystone ", "OK"]])
        else:
            infra.display_on_terminal(self, "Keystone Endpoint Check: FAIL")
            infra.add_table_rows(self, self.table_endpoint_check, [["Keystone ", "FAIL"]])
    
    def glance_endpoint_check(self, glance_instance):
        status, message, image_list = glance_instance.glance_image_list()
        if status == 200:
            infra.display_on_terminal(self, "Glance endpoint Check: OK")
            infra.add_table_rows(self, self.table_endpoint_check, [["Glance ", "OK"]])
        else:
            infra.display_on_terminal(self, "Glance endpoint Check: FAILED")
            infra.add_table_rows(self, self.table_endpoint_check, [["Glance ", "FAIL"]])
    
    def cinder_endpoint_check(self, cinder_instance):
        status, message, cinder_list = cinder_instance.cinder_list()
        if status == 200:
            infra.display_on_terminal(self, "Cinder endpoint Check : OK")
            infra.add_table_rows(self, self.table_endpoint_check, [["Cinder ", "OK"]])
        else:
            infra.display_on_terminal(self, "Cinder endpoint Check: FAILED")
            infra.add_table_rows(self, self.table_endpoint_check, [["Cinder ", "FAIL"]])
        
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
