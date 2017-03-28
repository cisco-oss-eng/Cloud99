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
import argparse
import paramiko

from cloud99.logging_setup import LOGGER


class SSH(object):
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def exec_command(self, cmd, get_pty=False):
        result = None
        error = None
        try:
            self.client.connect(hostname=self.host, username=self.user,
                                password=self.password)
            _, stdout, stderr = self.client.exec_command(cmd, get_pty)
        except paramiko.AuthenticationException, ex:
            LOGGER.exception("Authentication failed while connecting {}@{}."
                             " Exception {}".format(self.user, self.host, ex))
            result = ''
            error = ex
        else:
            # TODO handle large output
            result = stdout.read()
            error = stderr.read()
        finally:
            self.client.close()
            return result, error


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('user')
    parser.add_argument('password')
    parser.add_argument('cmd')
    args = parser.parse_args()
    ssh = SSH(args.host, user=args.user, password=args.password)
    out, err = ssh.exec_command(args.cmd)
    print "Out ", out
    print "Err ", err
