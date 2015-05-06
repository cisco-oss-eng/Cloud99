from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra

LOG = infra.ha_logging(__name__)

class NodeDisruptor(BaseDisruptor):

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
        while infra.is_execution_completed(self.finish_execution) is False:

            infra.display_on_terminal(self, "Rebooting the node ** ")
            time.sleep(1)
        '''
        infra.display_on_terminal(self, "Exiting the Baremetal Plugin")

    def process_disruption(self, sync=None, finish_execution=None):
        pass

    def start_disruption(self, sync=None, finish_execution=None):
        pass

    def is_module_exeution_completed(self):
        return infra.is_execution_completed(finish_execution=
                                            self.finish_execution)

    def stop_disruption(self):
        pass

    def set_report(self):
        pass

    def display_report(self):
        pass

    def baremetal_disruption(self, sync=None, finish_execution=None):
        pass

