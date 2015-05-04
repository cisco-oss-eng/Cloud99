from disruptors.baseDisruptor import BaseDisruptor
import ha_engine.ha_infra as infra
import time
import ssh.sshutils as ssh

LOG = infra.ha_logging(__name__)

class ServiceDisruptor(BaseDisruptor):
    report_headers = ['state', 'type', 'uptime']
    ha_report = []
    sync = None
    finish_execution = None

    def start_disruption(self, sync=None, finish_execution=None):
        print "inside service disruptors"
        self.sync = sync
        self.finish_execution = finish_execution
        LOG.info('Executing service Disruption... ')
        id = super(ServiceDisruptor, self).get_my_id()
        input_args = super(ServiceDisruptor, self).get_input_arguments()
        # print dir(input_args)
        # LOG.debug("Args %s", str(input_args))
        value = input_args.items()[0][1]

        # waiting for runner notification
        if sync:
            LOG.info("DISRUPTOR Going to wait......... ")
            sync.wait()

        while infra.is_execution_completed(self.finish_execution) is False:
            LOG.info("STOPING XXXXXX")
            time.sleep(2)
            LOG.info("STARTING ------")
            '''
            # session = ssh.SSH('oscontroller','10.126.243.35',
            password ='ospass1!')
            session = ssh.SSH(value.get('username'),value.get('ip'),
                              password=value.get('password'))
            # perform the needed operations here
            #print session.execute('ls')

            ret = session.execute(
            'systemctl stop openstack-nova-consoleauth.service')
            print ret
            '''

    def is_module_exeution_completed(self):
        return infra.is_execution_completed(
            finish_execution=self.finish_execution)

    def stop_disruption(self):
            pass

    def set_report(self):
        self.ha_report.append(['destorying', 'service-1', '5'])
        self.ha_report.append(['destroying', 'service-2', '10'])

    def display_report(self):
        return {'headers' : self.report_headers,
                'values' : self.ha_report }


# session = ssh.SSH('oscontroller','10.126.243.35',password ='ospass1!')
# print session
