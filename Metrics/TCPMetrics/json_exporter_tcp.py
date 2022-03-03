from prometheus_client import start_http_server, Metric, REGISTRY
import yaml
import json
import sys
import time
import os
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

        count = 1
        for entry in response:
          try:
            metricName = "Packet_" + str(count) + "_Scrape_" + str(output[6:-5]).replace("-","_")
            metric = Metric(metricName, 'Packet Info Collected from TCPDUMP', 'summary')
            metric.add_sample(metricName, value=1, labels={'TCP Source Port': entry['_source']['layers']['tcp']['tcp.srcport']})
            metric.add_sample(metricName, value=1, labels={'TCP Destination Port': entry['_source']['layers']['tcp']['tcp.dstport']})
            metric.add_sample(metricName, value=1, labels={'TCP Flags': entry['_source']['layers']['tcp']['tcp.flags']})
            metric.add_sample(metricName, value=1, labels={'TCP Window Size': entry['_source']['layers']['tcp']['tcp.window_size_value']})
            metric.add_sample(metricName, value=1, labels={'TCP Payload': entry['_source']['layers']['tcp']['tcp.payload']})
            metric.add_sample(metricName, value=1, labels={'IP Source': entry['_source']['layers']['ip']['ip.src']})
            metric.add_sample(metricName, value=1, labels={'IP Destination': entry['_source']['layers']['ip']['ip.dst']})
            metric.add_sample(metricName, value=1, labels={'IP Source Geo Summary': entry['_source']['layers']['ip']['ip.geoip.src_summary']})
            metric.add_sample(metricName, value=1, labels={'IP Source Latitude': entry['_source']['layers']['ip']['ip.geoip.src_summary_tree']['ip.geoip.src_lat']})
            metric.add_sample(metricName, value=1, labels={'IP Source Longitude': entry['_source']['layers']['ip']['ip.geoip.src_summary_tree']['ip.geoip.src_lon']})
            metric.add_sample(metricName, value=1, labels={'IP Destination Geo Summary': entry['_source']['layers']['ip']['ip.geoip.dst_summary']})
            metric.add_sample(metricName, value=1, labels={'IP Source Latitude': entry['_source']['layers']['ip']['ip.geoip.dst_summary_tree']['ip.geoip.dst_lat']})
            metric.add_sample(metricName, value=1, labels={'IP Source Longitude': entry['_source']['layers']['ip']['ip.geoip.dst_summary_tree']['ip.geoip.dst_lon']})
            metric.add_sample(metricName, value=1, labels={'Eth Source': entry['_source']['layers']['eth']['eth.src']})
            metric.add_sample(metricName, value=1, labels={'Eth Destination': entry['_source']['layers']['eth']['eth.dst']})
            metric.add_sample(metricName, value=1, labels={'Frame Protocols': entry['_source']['layers']['frame']['frame.protocols']})
            count += 1
            yield metric
          except KeyError:
            continue

        mName = "TCPDUMP_Retrieved_Packet_Count_From_Scrape_" + output[6:-5].replace("-","_")
        metric = Metric(mName, "Number of Packets Retrieved from TCPDUMP", "summary")
        metric.add_sample(mName, value=(count-1), labels={})
        yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  data = {}
  with open(sys.argv[1], 'r') as stream:
      try:
          data = yaml.safe_load(stream)
      except yaml.YAMLError as exc:
          print("Config file load error!")

  start_http_server(int(data['tcpPort']))
  REGISTRY.register(JsonCollector())
  while True: time.sleep(int(data['scrapeDuration']))
