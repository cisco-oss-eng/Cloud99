from monitors.baseMonitor import BaseMonitor
import ha_engine.ha_infra as common

LOG = common.ha_logging(__name__)

class Neutron(BaseMonitor):

    def start(self):
        LOG.info('Monitoring Neutron... ')

    def stop(self):
        LOG.info("Stopping Neutron...")

    def report(self):
        self.ha_report.append(self.report)

    def notify(self, *args, **kwargs):
        LOG.info('Args is  %s', str(args))
        for key, value in kwargs.iteritems():
            LOG.info('Got Notification with key %s, value %s' %(key, value))


