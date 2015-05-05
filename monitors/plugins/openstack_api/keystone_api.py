from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.exceptions import ClientException

class KeystoneHealth(object):
    def __init__(self, creds):
        self.keystoneclient = keystone_client.Client(**creds)
    
    def keystone_service_list(self):
        try:
            service_list = self.keystoneclient.services.list()
        except (ClientException, Exception) as e:
            return (404, e.message, [])
        return (200, "success", service_list)
    
    def keystone_endpoint_find(self, service_type, endpoint_type='publicURL'):
        return self.keystoneclient.service_catalog.url_for(service_type=service_type, endpoint_type=endpoint_type)
    
    def keystone_return_authtoken(self):
        return self.keystoneclient.auth_token
        
    
            
        
