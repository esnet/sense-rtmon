from prometheus_client import start_http_server, Metric, REGISTRY
import yaml
import json
import sys
import time
import requests
import os
from subprocess import Popen, PIPE

config_data ={}
if __name__ == '__main__':
  owd = os.getcwd()
  os.chdir("etc")
  os.chdir("tcp_exporter")
  infpth = str(os.path.abspath(os.curdir)) + "/tcp.yml"
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
        with open(complete, 'r', encoding="utf-8") as f:
          response = json.load(f)
        count = 1

        # delete previous urls 
        for each_url in delete_list:
            delete = requests.delete(each_url)
        delete_list = []
        
        for entry in response:
          try:
            metricName = "Packet_" + str(count) + "_Scrape_"
            metric = Metric(metricName, 'Packet Info Collected from TCPDUMP', 'summary')
            metric.add_sample(metricName, value=1, labels={'TCPSourcePort': entry['_source']['layers']['tcp']['tcp.srcport']})
            metric.add_sample(metricName, value=1, labels={'TCPDestinationPort': entry['_source']['layers']['tcp']['tcp.dstport']})
            metric.add_sample(metricName, value=1, labels={'TCPFlags': entry['_source']['layers']['tcp']['tcp.flags']})
            metric.add_sample(metricName, value=1, labels={'TCPWindowSize': entry['_source']['layers']['tcp']['tcp.window_size_value']})
            metric.add_sample(metricName, value=1, labels={'TCPPayload': entry['_source']['layers']['tcp']['tcp.payload']})
            metric.add_sample(metricName, value=1, labels={'IPSource': entry['_source']['layers']['ip']['ip.src']})
            metric.add_sample(metricName, value=1, labels={'IPDestination': entry['_source']['layers']['ip']['ip.dst']})
            metric.add_sample(metricName, value=1, labels={'IPSourceGeoSummary': entry['_source']['layers']['ip']['ip.geoip.src_summary']})
            metric.add_sample(metricName, value=1, labels={'IPSourceLatitude': entry['_source']['layers']['ip']['ip.geoip.src_summary_tree']['ip.geoip.src_lat']})
            metric.add_sample(metricName, value=1, labels={'IPSourceLongitude': entry['_source']['layers']['ip']['ip.geoip.src_summary_tree']['ip.geoip.src_lon']})
            metric.add_sample(metricName, value=1, labels={'IPDestinationGeoSummary': entry['_source']['layers']['ip']['ip.geoip.dst_summary']})
            metric.add_sample(metricName, value=1, labels={'IPSourceLatitude': entry['_source']['layers']['ip']['ip.geoip.dst_summary_tree']['ip.geoip.dst_lat']})
            metric.add_sample(metricName, value=1, labels={'IPSourceLongitude': entry['_source']['layers']['ip']['ip.geoip.dst_summary_tree']['ip.geoip.dst_lon']})
            metric.add_sample(metricName, value=1, labels={'EthSource': entry['_source']['layers']['eth']['eth.src']})
            metric.add_sample(metricName, value=1, labels={'EthDestination': entry['_source']['layers']['eth']['eth.dst']})
            metric.add_sample(metricName, value=1, labels={'FrameProtocols': entry['_source']['layers']['frame']['frame.protocols']})
            
            # arbitrary pay load data is stored inside url
            payload = "TCP_packet " + str(count) + "\n" 
            url = receiver_ip_address + ":9091/metrics/job/tcpMetrics/tcpSourcePort/" + str(entry['_source']['layers']['tcp']['tcp.srcport']) + "/tcpDestinationPort/" + str(entry['_source']['layers']['tcp']['tcp.dstport']) + "/TCPWindowSize/" + str(entry['_source']['layers']['tcp']['tcp.window_size_value']) + "/TCPFlags/" + str(entry['_source']['layers']['tcp']['tcp.flags']) +"/IPSource/" + str(entry['_source']['layers']['ip']['ip.src']) + "/IPDestination/" + str(entry['_source']['layers']['ip']['ip.dst'])
            push = requests.post(url, data=payload)
            delete_list.append(url)
            count += 1
            yield metric
          except KeyError:
            continue

        mName = "TCP_Packet_Count"
        metric = Metric(mName, "Number of Packets Retrieved from TCPDUMP", "summary")
        metric.add_sample(mName, value=(count-1), labels={})
        url2 = f"{receiver_ip_address}:9091/metrics/job/arpMetrics/instance/{instance_ip}/packetCount/value"
        payload2 = f"TCP_Packet_Count {str(count-1)}\n"
        push2 = requests.post(url2, data=payload2)
        yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  start_http_server(int(config_data['tcpMetrics']['port']))
  REGISTRY.register(JsonCollector())
  while True: time.sleep(int(config_data['tcpMetrics']['scrapeDuration']))
