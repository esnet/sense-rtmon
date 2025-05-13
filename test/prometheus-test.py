from prometheus_api_client import PrometheusConnect
import requests
from requests.auth import HTTPBasicAuth

# Create a session with basic auth
session = requests.Session()
session.auth = HTTPBasicAuth("sunami", "g20m5tulen@")

# Initialize PrometheusConnect with the session
prom = PrometheusConnect(
    url="http://autogole-prometheus.nrp-nautilus.io",
    session=session,
    disable_ssl=True  # only needed for HTTP
)

# Query
query = 'count(increase(interface_statistics{Key="ifHCInOctets", sitename="NRM_CENIC", hostname="aristaeos_s0"}[24h])) or on() vector(0)'
result = prom.custom_query(query=query)
print(result)
# Get result
if result:
    value = result[0].get('value', [None, None])[1]
    print("Query result:", value)
else:
    print("No data returned.")
