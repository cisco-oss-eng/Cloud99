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
            module_args='ls',
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


'''
ins = AnsibleRunner('svl6-csl-b-glancectl-002','root','')

ins = AnsibleRunner(host='10.126.243.35',remote_user='oscontroller',remote_pass='ospass1!')
ret= ins.do_reboot()
print ret


ins = AnsibleRunner(host='10.126.243.35',remote_user='oscontroller',remote_pass='ospass1!')
ret= ins.copy('output','/tmp/','/tmp/')
print ret

'''
ins = AnsibleRunner('svl4-csm-a-infra-001','root','Nimbus123*',sudo=True)
# ins = AnsibleRunner('192.168.56.101','openstack','password')
ret = ins.shell('python /tmp/jump_script.py %s "%s" %s >>/tmp/output'%('stop',['svl6-csl-b-glancectl-002'],'service openstack-glance-api stop'))
print ret

