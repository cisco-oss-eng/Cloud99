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
    
    
