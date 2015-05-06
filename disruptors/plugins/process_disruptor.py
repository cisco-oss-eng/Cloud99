from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra

LOG = infra.ha_logging(__name__)


class ProcessDisruptor(BaseDisruptor):

    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def process_disruption(self, sync=None, finish_execution=None):
        self.sync = sync
        self.finish_execution = finish_execution
        infra.display_on_terminal(self, "Entering  Process Disruption plugin")
        input_args = self.get_input_arguments()
        host_config = infra.get_openstack_config()

        infra.display_on_terminal(self, "Plugin Args -> ", str(input_args))
        infra.display_on_terminal(self, "Openstack Config -> ", str(host_config))

    def node_disruption(self, sync=None, finish_execution=None):
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



