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

import subprocess

from cloud99 import LOGGER


class Xterm(object):
    position = {
        'monitors': [
            "100x35+100+" + str(int(i * 100) + (i * 100)) for i in range(10)
            ],
        'disruptors': [
            "100x35-100+" + str(int(100) + (i * 100)) for i in range(10)
            ],
        'loaders': [
            "100x35-100-" + str(int(100) + (i * 100)) for i in range(10)
            ]
    }

    background = {
        'disruptors': 'DarkGray',
        'monitors': 'MintCream',
        'loaders': 'LightCyan1'
    }

    @staticmethod
    def get_position(plugin):
            if Xterm.position.get(plugin, None):
                return Xterm.position[plugin].pop(0)

    @staticmethod
    def show(xterm_for, module_name, node, pipe_path):
        LOGGER.info("XTERM of %s will read from %s", node, pipe_path)
        xterm_bg = Xterm.background.get(xterm_for, 'black')
        xterm_fg = 'black'
        pos = Xterm.get_position(xterm_for)
        subprocess.Popen(['xterm',
                          '-T', module_name.upper(),
                          '-fg', xterm_fg,
                          '-bg', xterm_bg,
                          '-fa', "'Courier New'", '-fs', '10',
                          '-geometry', pos,
                          '-e',
                          'tail', '-f', pipe_path])
