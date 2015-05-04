import unittest
from utils.config_yaml_parser import YamlParser


class ParserTest(unittest.TestCase):
    def test_input_file_by_printing(self):
        yml = YamlParser()
        print "Disruptor Level =  " + str(yml.get_disruptor_interval())
        print "Disruptor Type = " + str(yml.get_disruptor_list())
        print "Runner List = " + str(yml.get_runner_list())
        print "Process List = " + str(yml.get_process_disruptor_list())

        print "Baremetal list = " + str(yml.get_baremetal_disruptor_list())
        print "Baremetal Info 1 = " + str(yml.get_baremetal_disruptor_info('node_1'))
        print "Baremetal Info 2 = " + str(yml.get_baremetal_disruptor_info('node_2'))
        print "Baremetal Info 3 = " + str(yml.get_baremetal_disruptor_info('node_3'))
        print "node 1 username = " + str(yml.get_baremetal_disruptor_node_username('node_1'))
        print "node 2 IP = " + str(yml.get_baremetal_disruptor_node_ip('node_2'))
        print "node 3 password = " + str(yml.get_baremetal_disruptor_node_password('node_3'))

        print "Runners List = " + str(yml.get_runner_list())



if __name__ == '__main__':
    unittest.main()