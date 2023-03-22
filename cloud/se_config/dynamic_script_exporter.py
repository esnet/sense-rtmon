import os
import json

raw_string = f'''
if curl {pushgateway} | grep ".*instance=\"{host1}\".*job=\"arpMetrics\".*"; then
    echo "{echo_name}{host=\"{host1}\"} 1";
else 
    echo "{echo_name}{host=\"{host1}\"} 0";
fi
'''