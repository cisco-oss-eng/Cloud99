from optparse import OptionParser
from ha_engine.ha_parser import HAParser
from ha_engine.ha_executor import HAExecutor
import ha_engine.ha_infra as common


LOG = common.ha_logging(__name__)  

def main(config_file): 
    parser = HAParser(config_file)
    executor = HAExecutor(parser)
    executor.run() 
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="config_file", 
                      action="store", type="string")
    (options, args) = parser.parse_args()
    config_file = options.config_file 
    main(config_file) 

