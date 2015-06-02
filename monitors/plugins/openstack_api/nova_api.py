from novaclient.client import Client
from novaclient.exceptions import ClientException
class NovaHealth(object):
    """
    Provides all the necessary API
    for nova health Check
    """
    def __init__(self, creden):
        self.novaclient = Client(**creden)
    
    def nova_service_list(self):
        """
        Get the list of nova services
        """
        try:
            service_list = self.novaclient.services.list()
        except (ClientException, Exception) as e:
            return (400, e.message, [])
        return (200, "success", service_list)
    
    def nova_stop_server(self,instance_name):
        """
        Stop the server using id
        """
        try:
            server = self.novaclient.servers.find(name = instance_name)
            id = server.id
            ret = self.novaclient.servers.stop(id)
            

        except (ClientException, Exception) as e:
            return (400, e.message, [])
        return (200, "success", ret)

    def nova_start_server(self,instance_name):
        """
        Start the server using id
        """
        try:
            server = self.novaclient.servers.find(name = instance_name)
            id = server.id
            ret = self.novaclient.servers.start(id)
            

        except (ClientException, Exception) as e:
            return (400, e.message, [])
        return (200, "success", ret)
    
