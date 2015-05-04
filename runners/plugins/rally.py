from runners.baseRunner import BaseRunner
import ha_engine.ha_infra as infra
import time

LOG = infra.ha_logging(__name__)

class RallyRunner(BaseRunner):

    def execute(self, sync=None, finish_execution=None):
        input_args = self.get_input_arguments()

        infra.display_on_terminal(self,"Executing Rally Scenario ===> %s", str(input_args))

        subscribers = infra.get_subscribers_list()
        infra.display_on_terminal(self, "My subscribers are %s", str(subscribers))

        if sync:
            infra.display_on_terminal(self,"Rally preparing...")
            rally_command = r"/usr/local/bin/rally -v task start " \
                            r"/Users/pradeech/harally/rally/rally_sanity.json"
            pattern = "Benchmarking... This can take a while..."
            out = infra.execute_the_command(rally_command, pattern=pattern)

            infra.display_on_terminal(self, "RAlly waiting for the initial setup....")
            if out:
                #time.sleep(2)
                infra.display_on_terminal(self,"Notifying all Waiters....")
                # notify all the threads waiting
                infra.notify_all_waiters(sync)

        for i in range(10):
            infra.display_on_terminal(self,"Rally Executing ..... ! .... ! .... ")
            time.sleep(2)

        infra.display_on_terminal(self, "Rally finished executing.....")
        # Let the infra know to complete
        infra.set_execution_completed(finish_execution)

    def setup(self):
       infra.display_on_terminal(self,"Setting up the runner")

    def teardown(self):
       infra.display_on_terminal(self,"Tearing down the runner")

    def notify(self, *args, **kwargs):
        infra.display_on_terminal(self,'Args is  %s', str(args))
        for key, value in kwargs.iteritems():
            infra.display_on_terminal(self,'Got Notification with key %s, value %s' %(key, value))

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