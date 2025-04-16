from prometheus_api_client import PrometheusConnect
import requests
from requests.auth import HTTPBasicAuth

class Prometheus:
    def __init__(self, **kwargs):
        super().__init__()
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')

    def p_get_query(self, query):
        session = requests.Session()
        prom_user = self.config.get("prometheus_username", None)
        prom_pass = self.config.get("prometheus_password", None)
        if prom_user and prom_pass:
            session.auth = HTTPBasicAuth(prom_user, prom_pass)
            
            prom_url = self.config.get("prometheus_url", None)
            if prom_url:
                prom = PrometheusConnect(
                    url=prom_url,
                    session=session,
                    disable_ssl=True 
                )
                result = prom.custom_query(query=query)
                """
                    [{'metric': {}, 'value': [1744821208.697, '96']}]
                    [{'metric': {}, 'value': [1744821055.783, '0']}]
                """
                if result:
                    return result[0].get('value', [None, None])[1]
            else:
                self.logger.error("Promethues URL missing in config.")
                return None
        else:
            self.logger.error("Promethues Authentication missing in config.")
            return None
    
    def p_count_interface_statistics(self, **kwargs):
        query = f'count(increase(interface_statistics{{Key="{self.config.get("prometheus_query_key", "ifHCInOctets")}", sitename="{kwargs["sitename"]}", hostname="{kwargs["hostname"]}"}}[24h])) or on() vector(0)'
        return self.p_get_query(query)
    
    def p_count_interfaces_rx_packets(self, **kwargs):
        query = f'count(increase(ifHCInUcastPkts{{Key="{self.config.get("prometheus_query_key", "ifHCInUcastPkts")}", sitename="{kwargs["sitename"]}", hostname="{kwargs["hostname"]}"}}[24h])) or on() vector(0)'
        return self.p_get_query(query)
    
    def p_get_switch_template(self, **kwargs):
        if self.p_count_interface_statistics(self, kwargs=kwargs) == 0:
            if self.p_count_interfaces_rx_packets(self, kwargs=kwargs) == 0:
                return None
            else:
                return "vpp"
        else:
            return "default"