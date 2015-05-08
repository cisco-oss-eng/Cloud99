

class graphData(object):
    def __init__(self,servicename,hostname=None,desc=None,status=None,ts=None,data=None):
        self.servicename = servicename
        self.hostname = hostname
        self.desc = desc
        self.status = status
        self.ts = ts
        self.data = data
        
    def getServiceName(self):
        return self.servicename
    
    def getHostName(self):
        return self.hostname
    
    def getDesc(self):
        return self.desc
    
    def getStatus(self):
        return self.status
    
    def getTS(self):
        return self.ts

    def getData(self):
        return self.data
