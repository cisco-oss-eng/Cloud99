from monitors.baseMonitor import BaseMonitor
from monitors.plugins.nagios_monitor.nagios_cfg_generator import NagiosConfigGen

class NagiosConfigSetter(BaseMonitor):

    def stop(self):
        pass

    def report(self):
        pass

    def stable(self):
        pass

    def is_module_exeution_completed(self, finish_exection):
        pass

    def start(self, sync=None, finish_execution=None):
        yhp = NagiosConfigGen()
        yhp.setOpenstackNodeIp()
        yhp.performNagiosServiceCheck()
        yhp.generateNagiosHostConfig()
        yhp.setOpenstackAppVmIp("appvmlist")
        yhp.printHostList()
        yhp.generateNagiosAppVmConfig()

