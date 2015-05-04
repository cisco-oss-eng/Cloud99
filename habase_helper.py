import threading

import ha_engine.ha_infra as common


LOG = common.ha_logging(__name__) 

def notification(execobj, notifyList, *args, **kwargs): 
    if notifyList == None: 
        LOG.critical('Nothing to notify' ) 
        return 
    if execobj == None: 
        LOG.critical('Error in sending notification') 
        common.ha_exit(0) 
    
    for notifier in notifyList: 
        LOG.info('send notification: %s - with value:  %s' %(notifier, kwargs)) 
        try:
            threading.Thread(target = execobj.resource_objs[notifier].notify, args=(args), kwargs= (kwargs)).start()
        except: 
            raise common.NotifyNotImplemented(notifier) 
