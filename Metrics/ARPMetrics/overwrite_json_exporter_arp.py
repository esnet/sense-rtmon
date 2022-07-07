from prometheus_client import start_http_server, Metric, REGISTRY,CollectorRegistry
import os
import yaml
import json
import requests
import sys
import time
from subprocess import Popen, PIPE

config_data ={}
if __name__ == '__main__':
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

class JsonCollector(object):
  def collect(self):
    # Fetch the JSON
    dir = str(os.getcwd()) + "/jsonFiles/"
    arpout_json = dir + "arpOut.json"
    f = open(arpout_json)
    lines = f.readlines()

    # loads the json format in
    response = []
    for line in lines[1:-1]:
      response.append(json.loads(line[:-2]))
    count = 1
    
    # delete previous urls
    delete_file_path = dir + "delete.json"
    with open(delete_file_path,"rt") as fp:
      load_delete = json.load(fp)
      for each_url in load_delete:
        delete = requests.delete(each_url)
    delete_list = []
    
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
      push = requests.post(url, data=payload)
      delete_list.append(url)
      count += 1
      yield metric

    # store delete list
    with open(delete_file_path,"wt") as fp:
      json.dump(delete_list,fp)

    # mName = "ARP_Entry_Count" + str(count) + "_Scrape"
    mName = "ARP_Entry_Count"
    metric = Metric(mName, "Number of ARP Entries", "summary")
    metric.add_sample(mName, value=(count-1), labels={})
    url2 = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/entryCount/value"
    payload2 = f"ARP_Entry_Count {str(count-1)}\n"
    push2 = requests.post(url2, data=payload2)
    yield metric

        
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  start_http_server(int(config_data['arpMetrics']['port']))
  # REGISTRY.register(JsonCollector())
  dir = str(os.getcwd()) + "/jsonFiles/"
  output_file =  dir + "arpOut.json"
  previous_file = dir + "prev.json"

  while True:
    # time.sleep(1)
    cur_file = open(output_file)
    cur_lines = cur_file.readlines()
    pre_file = open(previous_file)
    pre_lines = pre_file.readlines()
    if pre_lines != cur_lines:
      REGISTRY.register(JsonCollector())
      time.sleep(1)
      REGISTRY = CollectorRegistry(auto_describe=True) # solves duplicate entry problem
    # CollectorRegistry.clear()

  # time.sleep(int(config_data['arpMetrics']['scrapeDuration']))
  # seems like nowhere to set scrape interval
