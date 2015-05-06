class HostObject(object):
    
    def __init__(self,host,ip,user,password,role,isNagios=False):
        self.host = host
        self.ip = ip
        self.user = user
        self.password = password
        self.isNagios = isNagios
        self.role = role

    def setNagios(self,isNagios):
        self.isNagios = isNagios

    def isNagiosRunning(self):
        return self.isNagios

    def getHost(self):
        return self.host

    def getIp(self):
        return self.ip

    def getUser(self):
        return self.user

    def getPassword(self):
        return self.password

    def getRole(self):
        return self.role

