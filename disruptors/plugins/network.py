from disruptors.baseDisruptor import BaseDisruptor

import ha_engine.ha_infra as common

LOG = common.ha_logging(__name__)

class NetworkDisruptor(BaseDisruptor):
    '''
    def __init__(self, **kwargs):
        super(BaseDisruptor, self).__init__(**kwargs)
        self.parameters = kwargs
        self.report_headers = ['state', 'type', 'uptime']
        self.ha_report = []
        # This is just dummy report
        self.gen_report()
    '''
    def start_disruption(self, sync=None, finish_execution=None):
        LOG.info('Executing Network Disruption... ')
        input_arguments = self.get_input_arguments()
        #self.send_notification(state = 'Started')


    def stop_disruption(self):
        for member, value in self.parameters.iteritems() :
            # based on the member you can terminate the process
            pass

    def gen_report(self):
        self.ha_report.append(['destorying', 'baremetal-1', '5'])
        self.ha_report.append(['destroying', 'baremetal-2', '10'])

    def report(self):
        return {'headers' : self.report_headers,
                'values' : self.ha_report }




