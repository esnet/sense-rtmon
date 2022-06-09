from prometheus_client import start_http_server, Metric, REGISTRY
import os
import yaml
import json
import requests
import sys
import time
from subprocess import Popen, PIPE

config_data ={}
if __name__ == '__main__':
  with open(sys.argv[1], 'r') as stream:
      try:
          config_data = yaml.safe_load(stream)
      except yaml.YAMLError as exc:
          print("Config file load error!")
receiver_ip_address = "http://" + str(config_data['receiverIP'])
instance_ip = "198.32.43.16"

class JsonCollector(object):
  def collect(self):
    delete_list = []
    dir = str(os.getcwd())
    loc = dir + "/jsonFiles/"
    pastOut = ""
    if os.listdir(loc) != []:
      p1 = Popen(["ls", "-t",  "*.json"], shell=True, stdout=PIPE, cwd=loc)
      p2 = Popen(["head", "-n1"], shell=True, stdin=p1.stdout, stdout=PIPE, cwd=loc)
      p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
      output = str(p2.communicate()[0].decode()).strip('\n').split('\n')[-1]
      if output != pastOut:
        pastOut = output
        complete = loc + output
        time.sleep(2)
        # Fetch the JSON
        f = open(complete)
        lines = f.readlines()
        response = []
        for line in lines[1:-1]:
          response.append(json.loads(line[:-2]))
        count = 1
        no_name = 0
        for each_url in delete_list:
            delete = requests.delete(each_url)
        delete_list = []
        for entry in response:
          try: 
            metricName = "ARP_Entry_" + str(count) + "_Scrape"
            metric = Metric(metricName, 'ARP Entry', 'summary')
            hostname = entry['hostname']
            if hostname == "?":
              hostname = "no_name" + str(no_name)
              no_name += 1
            else:
              hostname = entry['hostname']
            metric.add_sample(metricName, value=1, labels={'hostname': hostname})
            metric.add_sample(metricName, value=1, labels={'mac_address': entry['mac']})
            metric.add_sample(metricName, value=1, labels={'ip_address': entry['ip']})
            payload = "ARP_Table " + str(count) + "\n"
            url = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/hostname/{str(hostname)}/mac_address/ {str(entry['mac'])}/ip_address/{str(entry['ip'])}"
            push = requests.post(url, data=payload)
            delete_list.append(url)
            count += 1
            yield metric
          except KeyError:
            continue

        mName = "ARP_Entry_Count" + str(count) + "_Scrape"
        metric = Metric("ARP_Entry_Count", "Number of ARP Entries", "summary")
        metric.add_sample("ARP_Entry_Count", value=(count-1), labels={})
        url2 = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/entryCount/value"
        payload2 = f"ARP_Entry_Count {str(count-1)}\n"
        push2 = requests.post(url2, data=payload2)
        yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  start_http_server(int(config_data['port']))
  REGISTRY.register(JsonCollector())
  while True: time.sleep(int(config_data['scrapeDuration']))