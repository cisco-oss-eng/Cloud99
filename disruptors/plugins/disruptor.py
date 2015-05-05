from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra
import time

import os

LOG = infra.ha_logging(__name__)

class Disruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def node_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution
        infra.display_on_terminal(self, "Entering the Baremetal")
        infra.display_on_terminal(self, "Executing Baremetal Disruption... ")
        input_args = self.get_input_arguments()
        host_config = infra.get_openstack_config()

        infra.display_on_terminal(self, "My input args are %s ", str(input_args))
        infra.display_on_terminal(self, "Openstack Config %s", str(host_config))
        '''
        if sync:
            infra.display_on_terminal(self, "DISRUPTOR Going to wait......... ")
            sync.wait()
        '''
        #infra.notify_all_waiters(sync)
        infra.display_on_terminal(self,
                                  "BAREMETAL DISRUPTOR GOT THE NOTIFICATION.... REBOOTING ")
        while infra.is_execution_completed(self.finish_execution) is False:

            infra.display_on_terminal(self, "REBOOTING THE NODE--------> ")
            #infra.ssh_and_execute_command()
            time.sleep(1)

        infra.display_on_terminal(self, "BAREMETAL TERMINATING.........")
        #self.send_notification(state = 'Started')

    def start_disruption(self, sync=None, finish_execution=None):
        pass

    def is_module_exeution_completed(self):
        return infra.is_execution_completed(finish_execution=self.finish_execution)

    def stop_disruption(self):
        for member, value in self.parameters.iteritems() :
            # based on the member you can terminate the process
            pass

    def set_report(self):
        self.ha_report.append(['destorying', 'baremetal-1', '5'])
        self.ha_report.append(['destroying', 'baremetal-2', '10'])

    def display_report(self):
        return {'headers' : self.report_headers,
                'values' : self.ha_report }


    def baremetal_disruption(self, sync=None, finish_execution=None):
        pass

