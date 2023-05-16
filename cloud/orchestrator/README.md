## Flow to API
`flow_to_api.py` script reads a configuration file from `config_flow` and turns the yaml format node configuration into a siterm dictionary format. 

An example of the siterm dictionary format is shown below:
[{'hostname': 'sdn-dtn-1-7.ultralight.org', 'hosttype': 'host',
             'type': 'arp-push', 'arp': on 'metadata': {'instance': 'sdn-dtn-1-7.ultralight.org', 'flow_id': 'unqiue_test_id'},
             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
             'resolution': '5'},
            'sdn-dtn-1-7.ultralight.org', 'hosttype': 'host',
             'type': 'prometheus-push', 'arp': on 'metadata': {'instance': 'sdn-dtn-1-7.ultralight.org', 'flow_id': 'unqiue_test_id'},
             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
             'resolution': '5'},
             {'hostname': 'dellos9_s0', 'hosttype': 'host',
             'type': 'prometheus-push', 'metadata': {'instance': 'dellos9_s0'},
             'gateway': 'dev2.virnao.com:9091', 'runtime': str(int(getUTCnow())+610),
             'resolution': '5'}]: