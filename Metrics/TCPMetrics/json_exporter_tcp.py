from prometheus_client import start_http_server, Metric, REGISTRY
import yaml
import json
import sys
import time
import requests
import os
from datetime import datetime
from subprocess import Popen, PIPE

class JsonCollector(object):
  def collect(self):
    # Fetch the JSON
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
        now  = datetime.now()
        count = 1
        for entry in response:
          try:
            metricName = "Packet_" + str(count) + "_Scrape_" + now.strftime("%Y_%m_%d_%H_%M_%S")
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
            payload = "Scrape_" + now.strftime("%Y_%m_%d_%H_%M_%S") + " 1\n"
            url = "http://localhost:9091/metrics/job/tcpMetrics/tcpSourcePort/" + str(entry['_source']['layers']['tcp']['tcp.srcport']) + "/tcpDestinationPort/" + str(entry['_source']['layers']['tcp']['tcp.dstport']) + "/TCPWindowSize/" + str(entry['_source']['layers']['tcp']['tcp.window_size_value']) + "/TCPFlags/" + str(entry['_source']['layers']['tcp']['tcp.flags']) +"/IPSource/" + str(entry['_source']['layers']['ip']['ip.src']) + "/IPDestination/" + str(entry['_source']['layers']['ip']['ip.dst'])
            push = requests.post(url, data=payload)
            count += 1
            yield metric
          except KeyError:
            continue

        mName = "TCP_Packet_Count"
        metric = Metric(mName, "Number of Packets Retrieved from TCPDUMP", "summary")
        metric.add_sample(mName, value=(count-1), labels={})
        url2 = "http://localhost:9091/metrics/job/tcpMetrics/packetCount/" + str(count-1)
        payload2 = "Scrape_" + now.strftime("%Y_%m_%d_%H_%M_%S") + " 1\n"
        push2 = requests.post(url2, data=payload2)
        yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  data = {}
  with open(sys.argv[1], 'r') as stream:
      try:
          data = yaml.safe_load(stream)
      except yaml.YAMLError as exc:
          print("Config file load error!")

  start_http_server(int(data['port']))
  REGISTRY.register(JsonCollector())
  while True: time.sleep(int(data['scrapeDuration']))