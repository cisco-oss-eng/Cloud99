import re
import subprocess
import json
import time
import datetime
import os

def parse_input_file(input_file):
    input_dict = {}
    print "Input file: " + str(input_file)
    data = open(input_file)
    input_data = json.load(data)
    for key in input_data.keys():
        d = {'rally_scenario_json': str(input_data[key]['rally_scenario_json'])}
        input_dict.update(d)
        d = {'vm': str(input_data[key]['executed_on_vm'])}
        input_dict.update(d)
        d = {'openrc': str(input_data[key]['openrc_file_path'])}
        input_dict.update(d)
        d = {'sleep': str(input_data[key]['ha_sleep_interval'])}
        input_dict.update(d)
        d = {'reboot_list': str(input_data[key]['reboot_list'])}
        input_dict.update(d)
        d = {'creds': str(input_data[key]['username:password'])}
        input_dict.update(d)
        d = {'disruptor_level': str(input_data[key]['disruptor_level'])}
        input_dict.update(d)

    data.close()
    return input_dict


def parse_rc(cloud_file):
    rc_dict = {}
    with open(cloud_file) as inf:
        for line in inf:
            if re.search("OS_(.*)=", line):
                s = line.replace("export", "").strip().split('=')
                rc = {s[0]: s[1].strip()}
                rc_dict.update(rc)

    return rc_dict


def simple_cmd_execute(cmd):
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).communicate()


def ping_ip_address(host, should_succeed=True):
    cmd = ['ping', '-c1', host]
    print "[INFO] Pinging the node %s with cmd = %s" % (host, cmd)
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.wait()

    return (proc.returncode == 0) == should_succeed


def wait_for_ping(node, timeout, check_interval):
    print "[!!!!] Waiting for the ping to succeed timeout = %i interval = %i " % (timeout, check_interval)
    start = time.time()
    while True:
        if ping_ip_address(node):
            print "Ping success"
            break
        time.sleep(check_interval)
        if time.time() - start > timeout:
            print "TIMEOUT EXCEEDED HOST not rebooted"
            break
    return

def get_absolute_path_for_file(path, file_name, splitdir=None):
    '''
    Return the filename in absolute path for any file
    passed as relative path.
    '''
    base = os.path.basename(path)
    if splitdir is not None:
        splitdir = splitdir + "/" + base
    else:
        splitdir = base

    if os.path.isabs(path):
        abs_file_path = os.path.join(path.split(splitdir)[0],
                                     file_name)
    else:
        abs_file = os.path.abspath(path)
        abs_file_path = os.path.join(abs_file.split(splitdir)[0],
                                     file_name)

    return abs_file_path

def get_monitor_timestamp():
    '''
    Return the timestamp that will be added to the
    results.
    '''
    dt = datetime.datetime.now()
    timestamp = "%s:%s:%s-%s/%s/%s" % (dt.hour, dt.minute, dt.second,
                                           dt.month, dt.day, dt.year)

    return timestamp
