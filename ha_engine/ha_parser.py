import os
import inspect
import yaml
import ha_engine.ha_infra as infra
import ha_engine.ha_infra as common
import time
from collections import OrderedDict

LOG = common.ha_logging(__name__)
DEBUG = common.DEBUG

FRAMEWORK_MODULES = ['disruptors', 'monitors', 'runners']
SUPPORTED_MODE = ['parallel', 'sequence']
BUILT_IN_CMDS = ['delay', 'mode', 'timer', 'repeat']
REPORT_CMDS = ['report']
GLOBAL_CMDS = ['config', 'repeat']
PUBLISHER_CMDS = ['publishers']
SUBSCRIBER_CMDS = ['subscribers']

class DuplicateKeyFound(Exception):
    pass

class UnknownValueForMode(Exception): 
    pass 

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """ To make sure the order of execution in the order of the yaml  
    input file. 
    """ 
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        keycheck = []
        loader.flatten_mapping(node)
        for key_node, value_node in node.value: 
            # Sanity check before execution 
            if key_node.value == 'mode': 
                if value_node.value not in SUPPORTED_MODE:
                    raise UnknownValueForMode(value_node.value) 
            # Check for the duplicate keys
            if key_node.value in keycheck: 
                raise DuplicateKeyFound(key_node.value)  
            else: 
                keycheck.append(key_node.value) 

        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    try: 
        return yaml.load(stream, OrderedLoader)
    except DuplicateKeyFound as duplicateError:
        LOG.critical('Duplicate key found: %s', duplicateError) 
        common.ha_exit(0)
    except UnknownValueForMode as modeError: 
        LOG.critical('Unsupported value for mode, '
                     'must be either "parallel" or "sequence" '
                     '- but got %s' %str(modeError))
        common.ha_exit(0) 
    except Exception as e:
        print 'Error in parsing'  + str(e) 
        common.ha_exit(0) 

@infra.singleton
class HAParser(object):
    def __init__(self, cfg_file=None): 
        """
        :param cfg_file: input configuration file for the HA framework
        """
        self.user_input_file = cfg_file
        self.parsed_disruptor_config = {}
        self.parsed_runner_config = {}
        self.parsed_executor_config = {}
        self.parsed_monitor_config = {}
        self.plugin_input_data = {}
        self.resource_dirs = []
        self.plugin_to_class_map = {}
        self.node_plugin_map = {}

        # base
        self.openstack_config = {}

        infra_source_path = os.environ.get('HAPATH', None)
        if infra_source_path is None:
            LOG.critical("Run the install.sh ** source install.sh **")
            common.ha_exit(0)

        self.parsed_executor_config = self.parse_and_load_input_file(
            self.user_input_file)

        self.parsed_disruptor_config = \
            self.parse_and_load_input_file(infra_source_path +
                                           "/configs/disruptors.yaml")
        self.parsed_monitor_config = \
            self.parse_and_load_input_file(infra_source_path +
                                           "/configs/monitors.yaml")
        self.parsed_runner_config = \
            self.parse_and_load_input_file(infra_source_path +
                                           "/configs/runners.yaml")

        # dump the parsed info from the user on the console
        common.dump_on_console(self.parsed_executor_config, "Executor Config")
        common.dump_on_console(self.parsed_disruptor_config, "Disruptor Config")
        common.dump_on_console(self.parsed_monitor_config, "Monitor Config")
        common.dump_on_console(self.parsed_runner_config, "Runner Config")

        self.load_plugins_and_create_map()

    def load_plugins_and_create_map(self):
        """
        Calling different member methods to populate
        the resource_path, type_resource and resource instance 
        variables
        """
        self.find_the_ha_infra_path()
        self.parse_openstack_config()
        self.map_user_input_to_available_plugins()
        self.map_plugins_to_class_and_create_instances()

    def find_the_ha_infra_path(self):
        """
        This method to validate and populate all the resource paths.
        Return _resource_dirs if all the paths are valid otherwise returns
        error and exit.
        """
        ha_infra_dir = os.environ.get('HAPATH', None)
        self.resource_dirs.append(ha_infra_dir)

    def map_plugins_to_class_and_create_instances(self):

        if self.resource_dirs is None:
            LOG.critical('Unable to map type and resources, can not proceed')
            common.ha_exit(0) 

        # Load all the plugin modules defined under the Framework dir
        plugin_dirs = []
        for path in self.resource_dirs:
            for dirpath, dirname, filenames in os.walk(path):
                dirpath_split = dirpath.split('/')
                if dirpath_split[len(dirpath_split)-1] in FRAMEWORK_MODULES:
                    LOG.info("Loading all the plugins under %s ", dirpath)
                    plugin_dirs.append(dirpath + "/plugins")

        for plugin_dir in plugin_dirs:
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and "__init__" not in filename:
                    try:
                        module = filename[:-3]
                        plugin_dir_name = plugin_dir.split("/")[-2]

                        module_name = plugin_dir_name+".plugins."+filename[:-3]
                        LOG.info("Loading the plugin %s", module_name)
                        loaded_mod = __import__(module_name,
                                                fromlist = [module_name])

                        # Load class from imported module
                        # class_name = self.get_class_name(module_name)
                        class_names = inspect.getmembers(loaded_mod,
                                                         inspect.isclass)
                        for clas_name in class_names:
                            if clas_name[0].lower().startswith('base'):
                                base_class_name = clas_name[0]
                                LOG.info("Loading the Class %s",
                                         base_class_name)
                                try:
                                    loaded_base_class = \
                                        getattr(loaded_mod, base_class_name)
                                    break
                                except AttributeError as err:
                                    LOG.critical("Cannot load base class %s "
                                                 "from mod %s",
                                                 base_class_name, loaded_mod)

                        for clas_name in class_names:
                            if not clas_name[0].lower().startswith('base'):
                                class_name = clas_name[0]
                                LOG.info("Loading the Class %s", class_name)
                                try:
                                    loaded_class = getattr(loaded_mod,
                                                           class_name)
                                    if issubclass(loaded_class,
                                                  loaded_base_class):
                                        break
                                except AttributeError as err:
                                    LOG.critical("Cannot load class %s "
                                                 "from mod %s",
                                                 class_name, loaded_mod)

                        # Create an instance of the class
                        file_mod_name = filename[:-3]
                        input_arg_key = plugin_dir_name + "::" + file_mod_name
                        input_arguments = self.plugin_input_data.get(
                            input_arg_key, None)
                        instance = loaded_class(input_arguments)
                        if instance:
                            self.plugin_to_class_map[filename[:-3]] = instance
                    except OSError as err:
                        if DEBUG:
                            LOG.debug("Loading Module %s failed, error = %s",
                                      module, err)
                            common.ha_exit(0)

        # in the end if type_resource is empty, nothing to run exit
        if not self.plugin_to_class_map:
            LOG.critical('Cannot map plugins and load the class')
            common.ha_exit(0) 
        else: 
            LOG.info('All plugins and classes loaded successfully')

        common.dump_on_console(self.plugin_to_class_map, "Plugin to Class Map")
        return self.plugin_to_class_map

    def get_resource_path(self):
        """
        Getter for all the resource directories 
        return the resource lists
        """
        return self.resource_dirs[:]

    def map_user_input_to_available_plugins(self):
        parsed_plugin_list = [self.parsed_disruptor_config,
                              self.parsed_monitor_config,
                              self.parsed_runner_config]

        for parsed_config_data in parsed_plugin_list:
            for plugin in parsed_config_data:
                plugin_data = parsed_config_data.get(plugin, None)
                if plugin_data:
                    for plugin_data_item in plugin_data:
                        for plugin_item, item_data in \
                                plugin_data[plugin_data_item].items():
                            plugin_key = (plugin + "::" + plugin_data_item
                                                 #+ "::" + plugin_item
                                                  )
                            self.node_plugin_map[plugin_item] = \
                                plugin_data_item
                            if self.plugin_input_data.get(plugin_key, None):
                                self.plugin_input_data.get(plugin_key).\
                                    append({plugin_item: item_data})
                            else:
                                self.plugin_input_data[plugin_key] = \
                                    [{plugin_item: item_data}]
                else:
                    LOG.warning("No input data given for plugin %s", plugin)

        common.dump_on_console(self.node_plugin_map, "Node Plugin Map")

    @staticmethod
    def parse_and_load_input_file(yaml_file):

        parsed_config_dict = OrderedDict()
        if yaml_file:
            infra.infra_assert(yaml_file is not None, "Config file is Missing")
            if os.path.isfile(yaml_file):
                LOG.info('Config file exists, start parsing ' +
                         str(yaml_file))
            else:
                infra.infra_assert(0 == 1, "Config file is Missing")
            with open(yaml_file, 'r') as fp:
                try:
                    parsed_config_dict = ordered_load(fp, yaml.SafeLoader)
                except yaml.error.YAMLError as error:
                    infra.infra_assert(0 == 1, error)

            # Make sure the resource is not None.
            infra.infra_assert(parsed_config_dict is not None,
                               "Yaml load failed")

        return parsed_config_dict

    def parse_openstack_config(self):
        openstack_config = os.environ.get('HAPATH', None)
        if openstack_config:
            complete_openstack_config = \
                openstack_config + "/configs/openstack_config.yaml"

        self.openstack_config = dict(self.parse_and_load_input_file(
            complete_openstack_config))
        '''
        disruptor_yaml = \
            openstack_config + "/configs/ha_configs/disruptors.yaml"

        if os.path.isfile(disruptor_yaml):
            os.remove(disruptor_yaml)

        new_dict = {}
        for key, data in self.openstack_config.items():
            new_dict[key] = dict(data)
        disruptor_dict = {'disruptors': {'disruptor': new_dict}}

        self.dump_dict_to_yaml(disruptor_dict, yaml_file=disruptor_yaml)
        self.parsed_disruptor_config = \
            self.parse_and_load_input_file(openstack_config +
                                           "/configs/ha_configs/disruptors.yaml")
        '''

    @staticmethod
    def dump_dict_to_yaml(data, yaml_file=None):
        """
        Method to dump the dict to a output yaml file
        """
        with open(yaml_file, "w+") as f:
            f.write(yaml.dump(data, default_flow_style=False))