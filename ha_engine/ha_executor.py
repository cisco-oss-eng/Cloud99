import threading
import multiprocessing
import subprocess
import inspect
from ha_engine import ha_parser
from ha_engine import ha_infra
import os
import shutil
import utils.utils as utils

LOG = ha_infra.ha_logging(__name__)


class HAExecutor(object):
    infra_path = "/tmp/ha_infra/"
    xterm_position = ["100x35-100-100", "100x35+100-100",
                      "100x35+100+100", "100x35-100+100"]*10
    xterm_bg = {'disruptors': 'DarkGray',
                'monitors': 'MintCream',
                'runners': 'LightCyan1'}

    def __init__(self, parser):
        """
        Get the resource form haparser as input parameter and creates
        all the objects that are needed to run the executor.
        """
        # Resoruce from haparser
        self.executor_threads = []
        self.executor_data = parser.parsed_executor_config
        self.plugin_to_class_map = parser.plugin_to_class_map
        self.node_plugin_map = parser.node_plugin_map
        self.module_plugin_map = parser.module_plugin_map
        self.sync_objects = {}
        self.finish_execution_objects = {}
        self.open_pipes = []

        if self.executor_data:
            ha_infra.dump_on_console(self.executor_data, "Executor Data")

        ha_infra.dump_on_console(self.plugin_to_class_map,
                                 "Plugins to Class map")

    def run(self):
        """
        Actual execution starts here
        """
        # Exit if the executor is not defined.
        execute = self.executor_data.get('executors', None)
        if execute is None:
            LOG.critical('Nothing to run')
            ha_infra.ha_exit(0)

        self.executor_threads = []
        # clean up the xterm paths
        if os.path.exists(self.infra_path):
            shutil.rmtree(self.infra_path)

        ha_infra.start_run_time = \
            utils.get_timestamp(complete_timestamp=True)

        user_env_pc = None
        if os.environ.get('PROMPT_COMMAND', None):
            # save the PROMPT_COMMAND to set xterm title for now
            user_env_pc = os.environ['PROMPT_COMMAND']
            del os.environ['PROMPT_COMMAND']

        for executor_index, executor_block in enumerate(execute):
                # Check whether the executor block needs to be repeated
                # process the repeat commandi
                if not executor_block:
                    ha_infra.stop_run_time = \
                        utils.get_timestamp(complete_timestamp=True)
                    LOG.info("******** Completing the execution ******** ")
                    ha_infra.ha_exit(0)

                parallel = False
                repeat_count = 1
                LOG.info('Executing %s' % str(executor_index+1))

                if 'repeat' in executor_block:
                    repeat_count = executor_block.get('repeat', 1)
                    executor_block.pop('repeat')

                use_sync = False
                if 'sync' in executor_block:
                    LOG.info("Sync is requested within the block")
                    use_sync = executor_block.get('sync', False)
                    LOG.info("Use Sync %s", use_sync)

                ha_interval = None
                if 'ha_interval' in executor_block:
                    ha_interval = executor_block.get('ha_interval', None)
                disruption_count = 1 
                if 'disruption_count' in executor_block:
                    disruption_count = executor_block.get('disruption_count',
                                                          None)
                 
                LOG.info("Block will be repeated %s times", repeat_count)
                # Repeat count in each steps
                for i in range(repeat_count):
                    LOG.info("******** Block Execution Count %s ********  ",
                             str(i+1))
                    # process the mdoe command
                    if 'mode' in executor_block:
                        # if mode is parallel set parllel flag
                        if executor_block['mode'].lower() == 'parallel':
                            LOG.info('starting thread')
                            parallel = True
                        elif executor_block['mode'].lower() == 'sequence':
                            LOG.info('sequential execution')
                        else:
                            LOG.critical('Unsupported mode , '
                                         'must be either '
                                         '"parallel" or "sequence"')
                            ha_infra.ha_exit(0)
                        executor_block.pop('mode')

                    # process the timer command
                    if 'timer' in executor_block:
                        # TODO: pradeech
                        LOG.info('Timer....')
                        executor_block.pop('timer')

                    try:
                        # Execute the command and the respective parameters
                        del self.executor_threads[:]

                        for step_action, nodes in executor_block.iteritems():
                            launched_process = 0
                            ha_infra.set_launched_process_count(
                                launched_process)
                            self.execute_the_block(executor_index,
                                                   nodes,
                                                   step_action,
                                                   ha_interval,
                                                   disruption_count,
                                                   parallel=parallel,
                                                   use_sync=use_sync)

                        if self.executor_threads:
                            # start all the executor threads
                            [t.start() for t in self.executor_threads]
                            [t.join() for t in self.executor_threads]

                        ha_infra.display_infra_report()
                    except NotImplementedError as runerror:
                        LOG.critical('Unable to execute %s - %s'
                                     % runerror, step_action)
                        ha_infra.ha_exit(0)

                    except Exception as runerror:
                        LOG.critical('Unable to continue execution %s'
                                     % str(runerror))
                        ha_infra.ha_exit(0)

        LOG.info("******** Completing the executions ******** ")
        ha_infra.stop_run_time = \
            utils.get_timestamp(complete_timestamp=True)

        # clean up all the pipes
        for f in self.open_pipes:
            os.unlink(f)
        # restore the env variables
        if user_env_pc:
            os.environ['PROMPT_COMMAND'] = user_env_pc

    def execute_the_block(self, executor_index, nodes, step_action,
                          ha_interval, disruption_count, parallel=False,
                          use_sync=False):

        use_process = False
        node_list = []
        if isinstance(nodes, list):
            node_list = nodes

        sync = None
        finish_execution = None

        if parallel:
            if use_sync:
                if self.sync_objects.get(executor_index, None):
                    sync = self.sync_objects[executor_index]
                else:
                    sync = multiprocessing.Event() if use_process\
                        else threading.Event()
                    self.sync_objects[executor_index] = sync
            if self.finish_execution_objects.get(executor_index, None):
                finish_execution = self.finish_execution_objects[executor_index]
            else:
                finish_execution = multiprocessing.Event() if use_process \
                    else threading.Event()
                self.finish_execution_objects[executor_index] = finish_execution

        for node in node_list:
            # find the module and class object of each node
            pipe_path = None
            module_name = self.node_plugin_map.get(node, None)
            if module_name is None:
                LOG.critical("Cannot find  module %s when trying to execute",
                             module_name)
            class_object = self.plugin_to_class_map[module_name.lower()]

            plugin_commands = \
                [member[0] for member in
                    inspect.getmembers(class_object,
                                       predicate=inspect.ismethod)]
            if step_action in ha_parser.REPORT_CMDS:
                LOG.info('DISPLAYING REPORT')
                pass
            elif step_action in plugin_commands:
                if parallel:
                    pipe_path_dir = self.infra_path + module_name

                    if not os.path.exists(pipe_path_dir):
                        LOG.info("Creating a file path for " + pipe_path_dir)
                        try:
                            original_umask = os.umask(0)
                            os.makedirs(pipe_path_dir, 0777)
                        finally:
                            os.umask(original_umask)

                    pipe_path = pipe_path_dir + "/" + node
                    LOG.info("Trying to create a pipe %s", pipe_path)

                    if os.path.exists(pipe_path):
                        LOG.info("Removing the previous pipe")
                        os.remove(pipe_path)
                    else:
                        LOG.info("Creating a pipe for the %s", node)
                        os.mkfifo(pipe_path)

                    self.open_pipes.append(pipe_path_dir)
                    pos = self.get_xterm_position()

                    ha_infra.total_launched_process += 1
                    LOG.info("XTERM of %s will read from %s", node, pipe_path)

                    plugin = self.module_plugin_map[module_name.lower()]

                    xterm_bg = self.xterm_bg.get(plugin, 'black')
                    xterm_fg = 'black'
                    subprocess.Popen(['xterm',
                                      '-T', module_name.upper(),
                                      '-fg', xterm_fg,
                                      '-bg', xterm_bg,
                                      '-fa', "'Monospace'", '-fs', '10',
                                      '-geometry', pos,
                                      '-e',
                                      'tail', '-f', pipe_path])
                    LOG.info("Creating a thread for %s", node)

                    if use_process:
                        '''
                        t = multiprocessing.Process(
                        target=self.execute_the_command,
                                                args=(class_object, node,
                                                      step_action, ha_interval,
                                                      disruption_count,
                                                      sync, finish_execution))
                        '''
                    else:
                        t = threading.Thread(target=self.execute_the_command,
                                             args=(class_object, node,
                                                   step_action, ha_interval,
                                                   disruption_count, sync,
                                                   finish_execution))
                    self.executor_threads.append(t)
                else:
                    LOG.critical("Sequence mode is not supported")
            elif step_action in ha_parser.BUILT_IN_CMDS:
                getattr(self, step_action)(node)
            else:
                LOG.critical('Unknown command: %s' % str(step_action))
                ha_infra.ha_exit(0)

    @staticmethod
    def execute_the_command(class_object, node, cmd, ha_interval, 
                            disruption_count, sync=None,
                            finish_execution=None):
        if class_object and cmd:
            entire_block_arguments = getattr(class_object,
                                             "get_input_arguments")()
            if isinstance(entire_block_arguments, dict):
                # we have already set the args
                pass
            if isinstance(entire_block_arguments, list):
                for block_arg in entire_block_arguments:
                    if node in block_arg:
                        actual_arguments = block_arg
                        getattr(class_object,
                                "set_input_arguments")(actual_arguments)
        if ha_interval:
            setattr(class_object, "ha_interval", ha_interval)
        if disruption_count:
            setattr(class_object, "disruption_count", disruption_count)

        getattr(class_object, cmd)(sync=sync,
                                   finish_execution=finish_execution)

    def get_xterm_position(self):
        return self.xterm_position.pop()

