import threading
import multiprocessing
import subprocess
import time
import inspect
from ha_engine import ha_parser
from ha_engine import ha_infra
import os
import signal
import sys

LOG = ha_infra.ha_logging(__name__)

class HAExecutor(object): 
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
        self.sync_objects = {}
        self.finish_execution_objects = {}
        self.open_pipes = []
        self.xterm_position = ["120x35-100-100", "120x35+100-100",
                               "120x35+100+100", "120x35-100+100"]

        if self.executor_data:
            ha_infra.dump_on_console(self.executor_data, "Executor Data")
        ha_infra.dump_on_console(self.plugin_to_class_map,
                                 "Plugin to class map")

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
        for executor_index, executor_block in enumerate(execute):
                parallel = False
                repeat_count = 1
                LOG.info('Executing %s' % str(executor_index+1))

                # Check whether the executor block needs to be repeated
                # process the repeat commandi
                if not executor_block:
                    LOG.info("******** Completing the execution ******** ")
                    ha_infra.ha_exit(0)

                if 'repeat' in executor_block:
                    repeat_count = executor_block.get('repeat', 1)
                    executor_block.pop('repeat')

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
                        LOG.info('Do timer related stuff..') 
                        hatimer = True 
                        executor_block.pop('timer')

                    try:
                        # Execute the command and the respective parameters
                        del self.executor_threads[:]
                        for step_action, nodes in executor_block.iteritems():
                            self.execute_the_block(executor_index,
                                                   nodes,
                                                   step_action,
                                                   executor_block,
                                                   parallel=parallel)

                        if self.executor_threads:
                            # start all the executor threads
                            [t.start() for t in self.executor_threads]
                            [t.join() for t in self.executor_threads]
                    except NotImplementedError as runerror: 
                        LOG.critical('Unable to execute %s - %s'
                                     % runerror, step_action)
                        ha_infra.ha_exit(0)

                    except ha_infra.NotifyNotImplemented as notifyerr:
                        LOG.critical('Notify is not implmented in %s '
                                     %(notifyerr))
                        ha_infra.ha_exit(0)

                    except Exception as runerror: 
                        LOG.critical('Unable to continue execution %s'
                                     %str(runerror))
                        ha_infra.ha_exit(0)

        LOG.info("******** Completing the executions ******** ")
        # clean up all the pipes
        for f in self.open_pipes:
            os.unlink(f)

    def execute_the_block(self, executor_index,
                          nodes, step_action, step_info, parallel=False):

        node_list = []
        if isinstance(nodes, list):
            node_list = nodes

        sync = None
        finish_execution = None
        if parallel:
            if self.sync_objects.get(executor_index, None):
                sync = self.sync_objects[executor_index]
            else:
                sync = threading.Event()
                self.sync_objects[executor_index] = sync
            if self.finish_execution_objects.get(executor_index, None):
                finish_execution = self.finish_execution_objects[executor_index]
            else:
                finish_execution = threading.Event()
                self.finish_execution_objects[executor_index] = finish_execution

        for node in node_list:
            # find the module and class object of each node
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
                ha_infra.display_report(class_object, step_action)
            elif step_action in ha_parser.PUBLISHER_CMDS:
                pass
            elif step_action in ha_parser.SUBSCRIBER_CMDS:
                ha_infra.add_subscribers_for_module(node, step_info)
            elif step_action in plugin_commands:
                if parallel:
                    print "Creating a thread for " + node

                    pipe_path = "/tmp/" + module_name
                    if not os.path.exists(pipe_path):
                        LOG.info("Creating a file path for " + pipe_path)
                        os.mkfifo(pipe_path)

                    self.open_pipes.append(pipe_path)
                    pos = self.get_xterm_position()
                    subprocess.Popen(['xterm', '-geometry', pos,  '-e', 'tail', '-f', pipe_path])
                    t = threading.Thread(target=self.execute_the_command,
                                                args=(class_object, step_action,
                                                sync, finish_execution))
                    self.executor_threads.append(t)
                else:
                    self.execute_the_command(class_object, step_action)
            elif step_action in ha_parser.BUILT_IN_CMDS:
                getattr(self, step_action)(node)
            else:
                LOG.critical('Unknown command: %s' % str(step_action))
                ha_infra.ha_exit(0)
    @staticmethod
    def execute_the_command(class_object, cmd, sync=None,
                            finish_execution=None):
        """
        Execute the command
        """
        if class_object and cmd:
             getattr(class_object, cmd)(sync=sync,
                                        finish_execution=finish_execution)

    @staticmethod
    def delay(self, val):
        """ 
        built-in-method for delay 
        """
        LOG.info('Waiting for %d seconds' %(val))
        time.sleep(val) 

    @staticmethod
    def timer(self, val): 
        LOG.info('Executing timer..') 

    def post(self, rsrc_obj):
        pass

    def remove_instance(self): 
        pass 

    def get_xterm_position(self):
        return self.xterm_position.pop()

def signal_term_handler(signal, fram):
    print "GOT SIGTERM ......"
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_term_handler)