#! /usr/bin/python
""" Fetch Kubernetes quotas from each namespaces and print related stats.
    tvass / UQAM

    Example : ./k8s_stat.py --kubeconfig="/path/to/kubeconfig" --filter=siad

    --kubeconfig : Default value set to "~/.kube/config".
    --filter : Namespaces starts with "string" (ie: siad). Don't use for NO filter.
    -- debug : Print debug info to screen

    In our case, there is 1 quota per NS, named "quota-namespace".
    Adapt code for your needs.
"""

import json
import subprocess
import shlex
import sys
import re
import getopt
from os.path import expanduser

total_request_cpu = total_request_mem = total_limit_cpu = total_limit_mem = float(0)

def setup():
    global _filter
    global _debug
    _filter = None
    _debug = None

    kubeconfig = expanduser("~")+"/.kube/config"
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dhk:f:', ["debug","help", "kubeconfig=","filter="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--debug"):
            _debug = 1
        elif opt in ("-k", "--kubeconfig"):
            kubeconfig = arg
        elif opt in ("-f", "--filter"):
            _filter = arg
    global _kubectl
    _kubectl = "/bin/kubectl --kubeconfig=\""+kubeconfig+"\" -o json "

def usage():
    print sys.argv[0]+" --kubeconfig=/path/to/kubeconfig --filter=starts_with_this_string"
    sys.exit()

def convert(mystring):
    if mystring.endswith('m'):
        return float(re.sub("[^0-9]", "",mystring))/1000
    if mystring.endswith('Ki'):
        return float(re.sub("[^0-9]", "",mystring))/1024
    if mystring.endswith('Mi'):
        return float(re.sub("[^0-9]", "",mystring))
    if mystring.endswith('Gi'):
        return float(re.sub("[^0-9]", "",mystring))*1024
    else:
        return float(mystring)

def fail(e):
    print "Error:", str(e)

setup()

"""
Get cluster stats (summ CPU/MEM)
"""
getnodes = _kubectl+"get nodes"

if(_debug):
    print getnodes

command_nodes = shlex.split(getnodes)
process_nodes = subprocess.Popen(command_nodes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output_nodes, err = process_nodes.communicate()

try:
        data = json.loads(output_nodes)
        total = len(data['items'])
        total_nodes = 0
        total_cpu = 0
        total_mem = 0
        for x in range (0,total):
            try:
                if(_debug):
                    print "Adding ... "+data['items'][x]['spec']['externalID']
                cpu = int(data['items'][x]['status']['allocatable']['cpu'])
                mem = data['items'][x]['status']['allocatable']['memory']
                total_nodes = total_nodes + 1
                total_cpu = total_cpu + cpu
                total_mem = total_mem + convert(mem)
            except ValueError, e:
                if(_debug):
                    print "No CPU/mem found for node"
except ValueError, e:
        fail(e)

"""
Get namespaces stats w/ quotas
"""
getnamespaces = _kubectl+"get namespaces"
if(_debug):
    print getnamespaces

command_namespace = shlex.split(getnamespaces)
process_namespace = subprocess.Popen(command_namespace, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output_namespace, err = process_namespace.communicate()

try:
        data = json.loads(output_namespace)
        total = len(data['items'])
        total_namespaces = 0
        for x in range (0,total):
            namespace = data['items'][x]['metadata']['name']
            getquota = _kubectl+"get quota/quota-"+namespace+" --namespace="+namespace
            try:
                command_quota = shlex.split(getquota)
                process_quota = subprocess.Popen(command_quota, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output_quota, err = process_quota.communicate()
                data_quota = json.loads(output_quota)
                request_cpu = data_quota['spec']['hard']['cpu']
                request_mem = data_quota['spec']['hard']['memory']
                limit_cpu = data_quota['spec']['hard']['limits.cpu']
                limit_mem = data_quota['spec']['hard']['limits.memory']
                if (_filter):
                    if namespace.startswith(_filter):
                        if(_debug):
                            print "Adding ... "+namespace
                        total_request_cpu = total_request_cpu + convert(request_cpu)
                        total_request_mem = total_request_mem + convert(request_mem)
                        total_limit_cpu   = total_limit_cpu   + convert(limit_cpu)
                        total_limit_mem   = total_limit_mem   + convert(limit_mem)
                        total_namespaces=total_namespaces+1
                    else:
                        if(_debug):
                            print "Skipping ... "+namespace
                else:
                    if(_debug):
                        print "Adding ... "+namespace
                    total_request_cpu = total_request_cpu + convert(request_cpu)
                    total_request_mem = total_request_mem + convert(request_mem)
                    total_limit_cpu   = total_limit_cpu   + convert(limit_cpu)
                    total_limit_mem   = total_limit_mem   + convert(limit_mem)
                    total_namespaces=total_namespaces+1
            except ValueError, e:
                if(_debug):
                    print "No quota for "+namespace

        if (_filter):
            print "Stats for "+_filter+" ("+str(total_namespaces)+" namespaces with quota):"
        else:
            print "Stats ("+str(total_namespaces)+" namespaces with quota):"
        print ""
        print "TOTAL CPU Request (core) ........ "  + str(total_request_cpu) + " (" +str(int(round(total_request_cpu/total_cpu*100))) + "%)"
        print "TOTAL CPU Limit   (core) ........ "  + str(total_limit_cpu) + " (" +str(int(round(total_limit_cpu/total_cpu*100))) + "%)"
        print "TOTAL MEM Request (Mi) .......... "  + str(total_request_mem) + " (" +str(int(round(total_request_mem/total_mem*100))) + "%)"
        print "TOTAL MEM Limit   (Mi) .......... "  + str(total_limit_mem) + " (" +str(int(round(total_limit_mem/total_mem*100))) + "%)"
except ValueError, e:
        fail(e)
