import ansible.runner
import ansible.inventory
import sys
import os

class AnsibleRunner(object):
    def __init__(self,
                 host=None,
                 remote_user=None,
                 remote_pass=None,
                 sudo=False):
        self.host_list = [host]
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.sudo = sudo
        self.inventory = ansible.inventory.Inventory(self.host_list)


    def do_reboot(self):
        runner = ansible.runner.Runner(
            module_name='command',
            module_args='reboot -f',
            remote_user=self.remote_user,
            remote_pass=self.remote_pass,
            inventory = self.inventory,
        )
        out = runner.run()
        if out['dark'].get(self.host_list[0],{}).get('msg') !=None and out['dark'].get(self.host_list[0],{}).get('failed') == True:
            sys.stderr.write('Error, %s\n'%out['dark'].get(self.host_list[0]).get('msg'))
            raise Exception(out['dark'].get(self.host_list[0]).get('msg'))
            # return
            # sys.exit()
        return out

    def execute_on_remote(self):
        yml = os.getcwd()+os.sep+'configs'+os.sep+'jump.yaml'
        out = os.system('ansible-playbook %s'%yml)
        return out

    def copy(self,filename,src,dest):
        runner = ansible.runner.Runner(
            module_name='copy',
            module_args='src=%s%s dest=%s'%(src,filename,dest),
            remote_user=self.remote_user,
            remote_pass=self.remote_pass,
            inventory = self.inventory,
        )
        out = runner.run()
        return out

    def fetch(self,filename,src,dest,flat='yes'):
        runner = ansible.runner.Runner(
            module_name='fetch',
            module_args='src=%s%s dest=%s flat=%s'%(src,filename,dest,flat),
            remote_user=self.remote_user,
            remote_pass=self.remote_pass,
            inventory = self.inventory,
        )
        out = runner.run()
        return out

    # can perform all shell operations Ex: rm /tmp/output
    def shell(self,command):
        runner = ansible.runner.Runner(
            module_name='shell',
            module_args=command,
            remote_user=self.remote_user, 
            remote_pass=self.remote_pass,
            inventory = self.inventory,
        )
        out = runner.run()
        return out        

