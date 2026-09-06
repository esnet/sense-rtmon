#!/usr/bin/env python3
# pylint: disable=line-too-long
"Class for interacting with Prometheus metrics using the prometheus-api-client library."
import traceback
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
        self.config = kwargs.get("config")
        self.logger = kwargs.get("logger")
        self.session = self.__connect()

    def __connect(self):
        session = requests.Session()
        prom_user = self.config.get("prometheus_username", None)
        prom_pass = self.config.get("prometheus_password", None)

        if prom_user and prom_pass:
            session.auth = HTTPBasicAuth(prom_user, prom_pass)
            return session
        return None

    def p_get_query(self, query):
        """
        Executes a PromQL query against the Prometheus server using basic auth and a custom session.
        Returns the value if available, or None on error or no data.
        """
        if not self.session:
            self.logger.error("Prometheus authentication missing in config or credentials not correct.")
            return None

        prom_url = self.config.get("prometheus_url", None)
        if prom_url:
            prom = PrometheusConnect(
                url=prom_url,
                session=self.session,
                disable_ssl=not prom_url.startswith("https"),
            )
            result = prom.custom_query(query=query)
            # Example result: [{'metric': {}, 'value': [timestamp, 'value']}]

            if result:
                return result[0].get("value", [None, None])[1]
            return None
        self.logger.error("Prometheus URL missing in config.")
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

    def p_count_host_statistics(self, **kwargs):
        """
        Constructs and executes a query to count the interface counters node_exporter
        reports for a host. Mirrors the metric hostflow.json graphs, so a zero here
        means those panels would render empty.
        """
        query = f'count(increase(node_network_receive_bytes_total{{instance=~"{kwargs["hostname"]}.*", sitename="{kwargs["sitename"]}"}}[24h])) or on() vector(0)'
        return self.p_get_query(query)

    def p_count_qos_status(self, **kwargs):
        """
        Constructs and executes a query to count the QoS reservation series
        SNMPMon reports for a device on the given VLANs. Mirrors what the QoS
        panel graphs, so a zero here means that panel would render empty.

        key1 is the device SNMPMon saw the reservation on. The VLANs come from
        the manifest and are what scopes the answer to this instance rather than
        to every reservation on the device.
        """
        query = f'count(qos_status{{sitename="{kwargs["sitename"]}", key1="{kwargs["hostname"]}", vlan=~"{kwargs["vlans"]}"}}) or on() vector(0)'
        return self.p_get_query(query)

    def _p_safe_count(self, func, **kwargs):
        """Run one of the count helpers and fold every failure into None.

        None means "could not answer" and is kept distinct from a real zero,
        because callers hide dashboard panels on a zero.
        """
        try:
            return func(**kwargs)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self.logger.error(f"Error querying Prometheus via {func.__name__}: {ex}")
            self.logger.error(traceback.format_exc())
            return None

    def p_get_switch_template_state(self, **kwargs):
        """
        Returns (templateType, available) for a switch.

        templateType is 'default' when interface_statistics are present, 'vpp' when
        only rx packets are, and None when neither is - unchanged from issue #167.
        available is True, False, or None when the question could not be answered.
        """
        stats = self._p_safe_count(self.p_count_interface_statistics, **kwargs)
        if stats is None:
            # Unanswered. Keep the historical default template, report unknown.
            return "default", None
        if stats != "0":
            return "default", True
        packets = self._p_safe_count(self.p_count_interfaces_rx_packets, **kwargs)
        if packets is None:
            return "default", None
        if packets != "0":
            return "vpp", True
        return None, False

    def p_check_host_available(self, **kwargs):
        """Returns the tri-state availability of host monitoring data."""
        count = self._p_safe_count(self.p_count_host_statistics, **kwargs)
        if count is None:
            return None
        return count != "0"

    def p_check_qos_available(self, **kwargs):
        """Returns the tri-state availability of QoS reservation data."""
        count = self._p_safe_count(self.p_count_qos_status, **kwargs)
        if count is None:
            return None
        return count != "0"
