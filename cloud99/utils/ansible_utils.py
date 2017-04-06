# Copyright 2015 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ansible.runner
import ansible.inventory
import sys
import os


class AnsibleRunner(object):

    def __init__(self, host=None, remote_user=None, remote_pass=None):
        self.host_list = [host]
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.inventory = ansible.inventory.Inventory(self.host_list)

    def do_reboot(self):
        module_name = 'command'
        module_args = 'reboot -f'
        out = self._exec(module_name, module_args)
        error_message = out['dark'].get(self.host_list[0], {}).get('msg')
        failed = out['dark'].get(self.host_list[0], {}).get('failed')
        if error_message and failed:
            sys.stderr.write('Error, {}\n'.format(error_message))
            raise Exception(error_message)
        return out

    @staticmethod
    def execute_on_remote():
        yml = os.getcwd() + os.sep + 'configs' + os.sep + 'jump.yaml'
        out = os.system('ansible-playbook %s' % yml)
        return out

    def copy(self, filename, src, dest):
        module_name = 'copy'
        module_args = 'src=%s%s dest=%s' % (src, filename, dest)
        return self._exec(module_name, module_args)

    def fetch(self, filename, src, dest, flat='yes'):
        module_name = 'fetch'
        module_args = 'src=%s%s dest=%s flat=%s' % (src, filename, dest, flat)
        return self._exec(module_name, module_args)

    def shell(self, command):
        module_name = 'shell'
        module_args = command
        return self._exec(module_name, module_args)

    def _exec(self, module_name, module_args):
        runner = ansible.runner.Runner(
            module_name=module_name,
            module_args=module_args,
            remote_user=self.remote_user,
            remote_pass=self.remote_pass,
            inventory=self.inventory,
        )
        out = runner.run()
        return out
