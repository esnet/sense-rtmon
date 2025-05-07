from prometheus_api_client import PrometheusConnect
import requests
from requests.auth import HTTPBasicAuth

class Prometheus:
    """
    Prometheus client wrapper for querying metrics using the prometheus-api-client library.

    This class handles authenticated requests to a Prometheus server and provides 
    utility functions to query specific network-related metrics such as interface statistics 
    and packet counts. Configuration and logging are passed via kwargs.

    Expected config keys:
    - 'prometheus_url': Base URL of the Prometheus server
    - 'prometheus_username': Username for HTTP Basic Auth
    - 'prometheus_password': Password for HTTP Basic Auth
    - 'prometheus_query_key': (Optional) Metric key to use in PromQL queries
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.session = self.__connect()

    def __connect(self):
        session = requests.Session()
        prom_user = self.config.get("prometheus_username", None)
        prom_pass = self.config.get("prometheus_password", None)

        if prom_user and prom_pass:
            session.auth = HTTPBasicAuth(prom_user, prom_pass)
            return session
        else:
            return None

    def p_get_query(self, query):
        """
        Executes a PromQL query against the Prometheus server using basic auth and a custom session.
        Returns the value if available, or None on error or no data.
        """

        if self.session:

            prom_url = self.config.get("prometheus_url", None)
            if prom_url:
                prom = PrometheusConnect(
                    url=prom_url,
                    session=self.session,
                    disable_ssl = False if prom_url.startswith('https') else True
                )
                result = prom.custom_query(query=query)
                # Example result: [{'metric': {}, 'value': [timestamp, 'value']}]

                if result:
                    return result[0].get('value', [None, None])[1]  
                else:
                    return None
            else:
                self.logger.error("Prometheus URL missing in config.")
                return None
        else:
            self.logger.error("Prometheus authentication missing in config or credentials not correct.")
            return None

    def p_count_interface_statistics(self, **kwargs):
        """
        Constructs and executes a query to count the number of interfaces reporting traffic stats.
        Uses the metric 'interface_statistics' and key from config (default: ifHCInOctets).
        """
        query = f'count(increase(interface_statistics{{Key="ifHCInOctets", sitename="{kwargs["sitename"]}", hostname="{kwargs["hostname"]}"}}[24h])) or on() vector(0)'
        return self.p_get_query(query)

    def p_count_interfaces_rx_packets(self, **kwargs):
        """
        Constructs and executes a query to count received unicast packets on interfaces.
        Uses the metric 'ifHCInUcastPkts' and key from config (default: ifHCInUcastPkts).
        """
        query = f'count(increase(interfaces_rx_packets{{Key="ifHCInUcastPkts", sitename="{kwargs["sitename"]}", hostname="{kwargs["hostname"]}"}}[24h])) or on() vector(0)'
        return self.p_get_query(query)

    def p_get_switch_template(self, **kwargs):
        """
        Returns a switch template type based on which Prometheus metrics are present.
        If neither interface_statistics nor unicast packet metrics are found, returns None.
        - Returns 'default' if interface_statistics are found.
        - Returns 'vpp' if only rx packets are found.
        """
        try:
            if self.p_count_interface_statistics(**kwargs) == '0':
                if self.p_count_interfaces_rx_packets(**kwargs) == '0':
                    return None
                else:
                    return "vpp"
            else:
                return "default"
        except:
            return None
