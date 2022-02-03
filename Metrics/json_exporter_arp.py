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
    lines = f.readlines()
    response = []
    for line in lines:
      response.append(json.loads(line))

    count = 1
    for entry in response:
      metricName = "ARP_Entry_" + str(count)
      metric = Metric(metricName, 'ARP Entry', 'summary')
      metric.add_sample(metricName, value=1, labels={'hostname': entry['hostname']})
      metric.add_sample(metricName, value=1, labels={'mac_address': entry['mac']})
      metric.add_sample(metricName, value=1, labels={'ip_address': entry['ip']})
      count += 1
      yield metric

    metric = Metric("ARP_Entry_Count", "Number of ARP Entries", "summary")
    metric.add_sample("ARP_Entry_Count", value=(count-1), labels={})
    yield metric
if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  start_http_server(int(sys.argv[1]))
  REGISTRY.register(JsonCollector(sys.argv[2]))

  while True: time.sleep(1)
