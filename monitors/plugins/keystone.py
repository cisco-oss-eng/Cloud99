from monitors.baseMonitor import BaseMonitor
import ha_engine.ha_infra as infra
import time
LOG = infra.ha_logging(__name__)

class Keystone(BaseMonitor):
    '''
    def __init__(self, **kwargs):
        self.parameters = kwargs
        self.report = None
    '''
    def start(self, sync=None, finish_execution=None):
        infra.display_on_terminal(self, 'Monitoring Keystone... ')
        input_args = self.get_input_arguments()
        infra.display_on_terminal(self, "Executing Keystone Service ===> %s",
                                  str(input_args))

        while True:
            infra.display_on_terminal(self, "Monitoring :) :) :)")
            time.sleep(2)

    def stop(self):
        infra.display_on_terminal(self, "Stopping the Keystone...")

    def set_report(self):
        self.ha_report.append(self.report)

    def get_report(self):
        infra.display_report(None)

    def notify(self, *args, **kwargs):
        infra.display_on_terminal(self, 'Args is  %s', str(args))
        for key, value in kwargs.iteritems():
            infra.display_on_terminal(self, 'Got Notification with key %s, value %s' %(key, value))


