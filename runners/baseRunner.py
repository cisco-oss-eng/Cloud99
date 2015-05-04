import ha_engine.ha_infra as common
import habase_helper as helper

LOG = common.ha_logging(__name__)


class BaseRunner(object):
    def __init__(self, input_args):
        self.ha_report = []
        self.input_args = {}

        if input_args:
            self.set_input_arguments(input_args)

    def set_input_arguments(self, input_args):

        self.input_args = input_args
        LOG.info("Self, input %s " , str(self.input_args))

    def get_input_arguments(self):
        return self.input_args

    def get_input_arguments(self):
        return self.input_args


    def execute(self, sync=None, finish_execution=None):
        raise NotImplementedError('Subclass should implement this method')

    def setup(self):
        raise NotImplementedError('Subclass should implement this method')

    def teardown(self):
        raise NotImplementedError('Subclass should implement this method')

    def set_report(self):
        raise NotImplementedError('Subclass should implement this method')

    def display_report(self):
        raise NotImplementedError('Subclass should implement this method')

    def stable(self):
        raise NotImplementedError('Subclass should implement this method')

    def is_module_exeution_completed(self, finish_exection):
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


