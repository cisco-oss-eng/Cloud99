from runners.baseRunner import BaseRunner
import ha_engine.ha_infra as infra
import time
import subprocess
import os
import threading
import Queue
import subprocess

LOG = infra.ha_logging(__name__)

class RallyRunner(BaseRunner):

    def execute(self, sync=None, finish_execution=None):
        input_args = self.get_input_arguments()
        infra.display_on_terminal(self, "Executing Rally Runner Plugin")

        if sync:
            infra.display_on_terminal(self, "Rally preparing...")
            rally_path = input_args[0]['rally_sanity']['rally_path']
            scenario_file = input_args[0]['rally_sanity']['scenario_file']
            rally_command = rally_path + " -v task start " + scenario_file

            pattern = "Benchmarking... This can take a while..."
            proc = subprocess.Popen(rally_command,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            line = ''
            while not(line == '' and proc.poll() is not None):
                line = proc.stdout.readline()
                if pattern in line:
                    infra.notify_all_waiters(sync)
                infra.display_on_terminal(self, line)

        infra.display_on_terminal(self, "Rally finished executing.....")
        # Let the infra know to complete
        infra.set_execution_completed(finish_execution)

    def setup(self):
       infra.display_on_terminal(self,"Setting up the runner")

    def teardown(self):
       infra.display_on_terminal(self,"Tearing down the runner")

    def is_module_exeution_completed(self, finish_exection):
        return infra.is_execution_completed(finish_execution=self.finish_execution)

    def gen_report(self):
        self.ha_report.append(['keystone', '600'])
        self.ha_report.append(['neutron', '600'])

    def set_report(self):
        report =  { 'headers' : ["Scenario Name", "Scenario Result"],
                 'values' :  ["LBAAS", "PASS"] }

    def display_report(self):
        return { 'headers' : ["Scenario Name", "Scenario Result"],
                 'values' :  [["LBAAS", "PASS"]] }


