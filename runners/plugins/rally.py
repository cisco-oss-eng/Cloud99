from runners.baseRunner import BaseRunner
import ha_engine.ha_infra as infra
import time
import subprocess
import os
import threading
import Queue
import subprocess
from fpdb import  ForkedPdb

LOG = infra.ha_logging(__name__)

class RallyRunner(BaseRunner):

    def execute(self, sync=None, finish_execution=None):
        input_args_dict = self.get_input_arguments()
        node_name = input_args_dict.keys()[0]
        input_args = input_args_dict.get(node_name, None)

        infra.display_on_terminal(self, "Executing Rally Runner Plugin ")

        infra.display_on_terminal(self, "Rally preparing...")
        rally_path = input_args['rally_path']
        scenario_file = input_args['scenario_file']
        rally_command = rally_path + " -v task start " + scenario_file

        infra.display_on_terminal(self, "Rally Path -> ", rally_path)
        infra.display_on_terminal(self, "Scenario file -> ", scenario_file)

        pattern = "Benchmarking... This can take a while..."
        infra.display_on_terminal(self, "Executing ", rally_command)
        proc = subprocess.Popen(rally_command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        line = ''
        while not(line == '' and proc.poll() is not None):
            line = proc.stdout.readline()
            if pattern in line:
                infra.display_on_terminal(self, "Notifying all waiters")
                infra.notify_all_waiters(sync)

            infra.display_on_terminal(self, line)

        results_command = rally_path + " task show "
        infra.display_on_terminal(self, "Collecting results ", results_command)
        proc = subprocess.Popen(results_command,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
        line = ''
        while not(line == '' and proc.poll() is not None):
            line = proc.stdout.readline()
            infra.display_on_terminal(self, line)

        # Let the infra know to complete
        infra.display_on_terminal(self, "Rally finished executing.....")
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


