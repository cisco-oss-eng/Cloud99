import paramiko
import sys

class SSH(object):
    def __init__(self,hostname,username=None,password=None,port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

    def ssh_command_exec(self,command):
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hostname,self.port,self.username,self.password)
            (stdin, stdout, stderr) = ssh.exec_command(command)
        except Exception,e:
            print e
        
        error = stderr.read()
        out = stdout.read()
        ssh.close()
        return {'hostname':self.hostname,'error':error,'result':out}

if __name__ == '__main__':
    ip_list = eval(sys.argv[1])
    command = sys.argv[2] # rhel process start/stop command
    ret = []
    for ip in ip_list:
        ret.append(SSH(ip,username ='root',password='').ssh_command_exec(command))
    print ret
