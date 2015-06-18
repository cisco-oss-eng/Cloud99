import ha_engine.ha_infra as infra

LOG = infra.ha_logging(__name__)


class BaseDisruptor(object):

    def __init__(self, input_args):
        self.ha_report = []
        self.input_args = {}

        if input_args:
            self.set_input_arguments(input_args)

    def set_input_arguments(self, input_args):
        self.input_args = input_args
        LOG.info("Self, input %s ", str(self.input_args))

    def get_input_arguments(self):
        return self.input_args

    def node_disruption(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def process_disruption(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def vm_disruption(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def jump_host_disruption(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')


    def start_disruption(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def stop_disruption(self, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def set_report(self):
        raise NotImplementedError('Subclass should implement this method')

    def display_report(self):
        raise NotImplementedError('Subclass should implement this method')

    def is_module_exeution_completed(self, finish_exection):
        raise NotImplementedError('Subclass should implement this method')

    def get_ha_interval(self):
        return self.ha_interval
 
    def get_disruption_count(self):
        return self.disruption_count

    def set_expected_failures(self):
        raise NotImplementedError('Subclass should implement this method')
