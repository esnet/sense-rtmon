from prometheus_client import start_http_server, Metric, REGISTRY
import json
import sys
import time

class JsonCollector(object):
  def __init__(self, endpoint):
    self._endpoint = endpoint
  def collect(self):
    # Fetch the JSON
    f = open(sys.argv[2])
    response = json.load(f)

    count = 1
    for entry in response:
      try:
        metricName = "Packet_" + str(count)
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

    metric = Metric("TCPDUMP_Retrieved_Packet_Count", "Number of Packets Retrieved from TCPDUMP", "summary")
    metric.add_sample("TCPDUMP_Retrieved_Packet_Count", value=(count-1), labels={})
    yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  start_http_server(int(sys.argv[1]))
  REGISTRY.register(JsonCollector(sys.argv[2]))

  while True: time.sleep(1)
