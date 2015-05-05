from cinderclient.client import Client
class CinderHealth(object):
    def __init__(self, creds):
        self.cinderclient = Client(**creds)
    
    def cinder_list(self):
        try:
            cinder_list = self.cinderclient.volumes.list()
        except Exception as e:
            return (404, e.message, [])
        return (200, "success" , cinder_list)
    
    
