import json
import os
import yaml
import sys
import re 

# configuration file path, system argument, the order it's in 
# e.g. python3 <file> abc.yml the order is 1
# e.g. python3 <file> <arg1> abc.yml the order is 2

def read_yml_file(path, sys_argv, order):
    # locate path
    owd = os.getcwd()
    os.chdir("..")
    config_path = str(os.path.abspath(os.curdir)) + path
    infpth = config_path + "/config.yml"
    os.chdir(owd)
    data = {}
    file_name = "config.yml"

    # argument given
    if len(sys_argv) > 1:
        file_name = str(sys_argv[order])
        file_path = config_path + "/" + file_name
        print(f"\n Config file {file_path}\n")
        with open(file_path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {file_path} could not be found in the config directory\n")
        
    else: # default config file
        with open(infpth, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(f"\n Config file {infpth} could not be found in the config directory\n")
    
    return data,file_name

# data,file_name = read_yml_file("config_site",sys.argv)