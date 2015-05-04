import utils
import yaml

HA = "HA"
DISRUPTOR = "DISRUPTOR"
RUNNER = "RUNNER"
MONITOR = "MONITOR"


class YamlParser(object):
    '''
    YAML Helper class.
    '''
    def __init__(self, yaml_file="../configs/input.yaml"):
        """
        Constructor
        :param yaml_file: path to the input file
        """
        self.yaml_file = yaml_file
        self.yaml_file = utils.get_absolute_path_for_file(__file__,
                                                           yaml_file)
        self.ymlparsed = None
        try:
            fp = open(yaml_file)
        except IOError as e:
            pass
            return

        try:
            self.ymlparsed = yaml.load(fp)
            print "self.ymlparsed: ", self.ymlparsed, dir(self.ymlparsed)
        except yaml.error.YAMLError as perr:
            return

    def get_disruptor_interval(self):
        """
        Method to return the disruptors interval
        -- the dirsuptors will be running at the
        specified interval
        -- If there is a list of disruptors, the
        disruptors will be executed in sequence
        and the process will be repeated after
        the specified interval
        """
        try:
            return self.get_option_value(HA, "disruptor_interval")
        except KeyError as kerr:
            print "Error: No disruptors interval specified"

    def get_disruptor_list(self):
        """
        Method to return the list of disruptors
        It could be just a single disruptors or
        a list of disruptors depending upon the
        input yaml file
        """
        try:
            return self.ymlparsed[DISRUPTOR].keys()
        except KeyError as kerr:
            print "Atleast one disruptors should be specified"

    def get_runner_list(self):
        """
        Method to return the list of runners
        """
        try:
            return self.ymlparsed[RUNNER].keys()
        except KeyError as kerr:
            print "Atleast one runner should be specified"

    def get_process_disruptor_list(self):
        """
        Method to get the list of process to be
        disrupted
        """
        try:
            if self.ymlparsed[DISRUPTOR].get('process'):
                return self.ymlparsed[DISRUPTOR].get('process')['process_list'].keys()
        except KeyError as kerr:
            print "Atleast one runner should be specified"

    def get_vm_disruptor_list(self):
        """
        Method to get the info for disrupting
        the service vms
        """

    def get_network_disruptor_info(self):
        """
        Method to get the info for disrupting
        the network
        """

    def get_baremetal_disruptor_list(self):
        """
        Method to get the info for disrupting
        the baremetal
        """
        try:
            baremetal_disruptor = self.ymlparsed[DISRUPTOR].get('baremetal')
            if baremetal_disruptor:
                node_list = list(baremetal_disruptor.keys())
            return node_list
        except KeyError as kerr:
            print "Baremetal info is not found"

    def get_baremetal_disruptor_info(self, node):
        """
        Method to get the info about a
        particular baremetal node
        """
        try:
            return self.ymlparsed[DISRUPTOR].get('baremetal').get(node)
        except KeyError as kerr:
            print "Information about %s is not found " % node

    def get_baremetal_disruptor_node_username(self, node):
        """
        Method to get the username of the node
        """
        try:
            return self.ymlparsed[DISRUPTOR].get('baremetal').get(node).get('username')
        except KeyError as kerr:
            print "Username not found for %s" % node

    def get_baremetal_disruptor_node_password(self, node):
        """
        Method to get the username of the node
        """
        try:
            return self.ymlparsed[DISRUPTOR].get('baremetal').get(node).get('password')
        except KeyError as kerr:
            print "Password  not found for %s" % node

    def get_baremetal_disruptor_node_ip(self, node):
        """
        Method to get the username of the node
        """
        try:
            return self.ymlparsed[DISRUPTOR].get('baremetal').get(node).get('ip')
        except KeyError as kerr:
            print "IP not found for %s" % node

    def run_ha_framework_in_parallel(self):
        """
        Method to tell whether run the 3 ha process in
        parallel or not
        """
        try:
            return self.get_option_value(HA, "parallel")
        except KeyError as kerr:
            print ""

    def get_monitor_service_list(self):
        """
        Method to return the list of services that has to be monitored
        """
        try:
            services_list = self.ymlparsed[MONITOR]
            return services_list
        except KeyError as kerr:
            print "No services list is proviced"

    def get_option_value(self, section, key):
        """
        Get the value of the key.
        What this returns is the specific value for a key within a section.
        """
        try:
            return self.ymlparsed[section][key]
        except KeyError as kerr:
            self.log.warning("Key Error: %s not found in %s. None returned",
                             kerr, section)
            return None


