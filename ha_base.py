import ha_engine.ha_infra as common
import habase_helper as helper

LOG = common.ha_logging(__name__) 


class HABase(object): 
    def __init__(self, **kwargs):
        self.ha_report = [] 
        if kwargs != None: 
            self.child_param = kwargs.get('param', None) 
            self.executor = kwargs.get('exec_obj', None) 

    def start(self, **kwags):
        raise NotImplementedError('Subclass should implement this method') 

    def stop(self): 
        raise NotImplementedError('Subclass should implement this method') 

    def report(self): 
        raise NotImplementedError('Subclass should implement this method') 

    def stable(self): 
        raise NotImplementedError('Subclass should implement this method') 

    def send_notification(self, *args, **kwargs): 
        if self.child_param != None: 
            notifyList = self.child_param.get('notification', None) 
            if notifyList != None: 
                helper.notification(self.executor, notifyList, *args, **kwargs) 
            else: 
                LOG.warning('Notification list is empty') 
        else: 
            LOG.warning('Notification list is not configured') 

    
