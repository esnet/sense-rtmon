from prometheus_client import start_http_server, Metric, REGISTRY,CollectorRegistry
import os
import yaml
import json
import requests
import sys
import time
from subprocess import Popen, PIPE
import subprocess

class JsonCollector(object):
  def collect(self):
    # Fetch the files see if any file has changed
    dir = str(os.getcwd())
    output_file =  dir + "/jsonFiles/arpOut.json"
    previous_file = dir + "/jsonFiles/prev.json"
    cur_file = open(output_file)
    cur_lines = cur_file.readlines()
    pre_file = open(previous_file)
    pre_lines = pre_file.readlines()
    time.sleep(0.25)
    
    ping_file_path =  dir + "/pingStat/ping_status.txt"
    ping_file =  open(ping_file_path)
    ping_lines = ping_file.readlines()
    previous_ping_file_path =  dir + "/pingStat/prev_ping_status.txt"
    previou_ping_file =  open(previous_ping_file_path)
    previous_ping_lines = previou_ping_file.readlines()
    
    time.sleep(0.25)
    if pre_lines != cur_lines or ping_lines != previous_ping_lines:
      cmd = f"yes | cp -rfa {output_file} {previous_file}"
      subprocess.run(cmd, shell=True)
      time.sleep(0.25)

      cmd2 = f"yes | cp -rfa {ping_file_path} {previous_ping_file_path}"
      subprocess.run(cmd2, shell=True)
      
      arpout_json = dir + "/jsonFiles/arpOut.json"
      f = open(arpout_json)
      lines = f.readlines()

      # loads the json format in
      response = []
      for line in lines[1:-1]:
        response.append(json.loads(line[:-2]))
      count = 1
      
      # delete previous urls
      delete_file_path = dir + "/jsonFiles/delete.json"
      with open(delete_file_path,"rt") as fp:
        # check if the file is empty
        if os.stat(delete_file_path).st_size != 0:
          load_delete = json.load(fp)
          for each_url in load_delete:
            requests.delete(each_url)
      delete_list = []
      
      time.sleep(0.25)
      # ping status sent here
      with open(ping_file_path,"rt") as fp:
        # check if the file is empty
        if os.stat(ping_file_path).st_size != 0:
          # cmd1 = f"echo \"running in ping\""
          # subprocess.run(cmd1, shell=True)
          clean_ping = ping_lines[0].strip()
          ping_url = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/ping_this_ip/{str(clean_ping)}"
          if clean_ping[-1] == "1":
            requests.post(ping_url, data="Success_1_failure_0 1\n")
          else:
            requests.post(ping_url, data="Success_1_failure_0 0\n")
          delete_list.append(ping_url)
          
          # switch_ping = ping_lines[1].strip()
          # switch_url = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/ping_this_ip/{str(switch_ping)}"
          # if switch_ping[-1] == "1":
          #   requests.post(switch_url, data="Success_1_failure_0 1\n")
          # else:
          #   requests.post(switch_url, data="Success_1_failure_0 0\n")
          # delete_list.append(switch_url)

      # post to pushgateway website
      for entry in response:
        metricName = "ARP_Entry_" + str(count) + "_Scrape"
        metric = Metric(metricName, 'ARP Entry', 'summary')
        hostname = entry['hostname']
        if hostname == "?":
          hostname = "no_name"
        else:
          hostname = entry['hostname']
        metric.add_sample(metricName, value=1, labels={'hostname': hostname})
        metric.add_sample(metricName, value=1, labels={'mac_address': entry['mac']})
        metric.add_sample(metricName, value=1, labels={'ip_address': entry['ip']})
        # arbitrary pay load data is stored inside url
        payload = "ARP_Table " + str(count) + "\n"
        url = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/hostname/{str(hostname)}/mac_address/{str(entry['mac'])}/ip_address/{str(entry['ip'])}"
        requests.post(url, data=payload)
        delete_list.append(url)
        count += 1
        yield metric

      # mName = "ARP_Entry_Count" + str(count) + "_Scrape"
      mName = "ARP_Entry_Count"
      metric = Metric(mName, "Number of ARP Entries", "summary")
      metric.add_sample(mName, value=(count-1), labels={})
      url2 = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/entryCount/value"
      payload2 = f"ARP_Entry_Count {str(count-1)}\n"
      requests.post(url2, data=payload2)
      delete_list.append(url2)
      yield metric

      # store delete list
      with open(delete_file_path,"wt") as fp:
        json.dump(delete_list,fp)
        
if __name__ == '__main__':
  config_data ={}
  owd = os.getcwd()
  os.chdir("etc")
  os.chdir("arp_exporter")
  infpth = str(os.path.abspath(os.curdir)) + "/arp.yml"
  os.chdir(owd)
  with open(infpth, 'r') as stream:
      try:
          config_data = yaml.safe_load(stream)
      except yaml.YAMLError as exc:
          print("Config file load error!")
  receiver_ip_address = "http://" + str(config_data['grafanaHostIP'])
  instance_ip = str(config_data['hostIP'])

  # Usage: json_exporter.py port endpoint
  start_http_server(int(config_data['arpMetrics']['port']))
  while True:
    REGISTRY.register(JsonCollector())
    time.sleep(1)
    REGISTRY = CollectorRegistry(auto_describe=True) # solves duplicate entry problem

  # time.sleep(int(config_data['arpMetrics']['scrapeDuration']))
  # seems like nowhere to set scrape interval
