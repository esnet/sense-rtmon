
import json
import os
import sys
import re 
import datetime
import cloud_functions


def fill_API(data, admin, password):
      
    now = datetime.datetime.now()
    
    current_time = now.strftime("%m/%d_%H:%M")  

    # curl the API key to here
    curlCMD = "curl -X POST -H \"Content-Type: application/json\" -d '{\"name\":\"" + str(current_time) + f'", "role": "Admin"}}\' http://{admin}:{password}@' + str('http://dev2.virnao.com:3000').split("//")[1] + "/api/auth/keys"
    token = os.popen(curlCMD).read()
    result = re.search('"key":"(.*)"}', str(token)) # extract the API key from result
    api_key = str(result.group(1))

    # write the API key into the data dictionary
    data['grafana_api_token'] = "Bearer " + api_key

    # write the API key to a file
    with open('api_key.txt', 'w') as file:
        file.write(api_key)
    print(api_key)

    return data , api_key

data = {
  "flow": "rtmon-beef7530-35a5-4cd4-8a79-9875e489242d",
  "title": "UCSD 2",
  "grafana_host": "http://dev2.virnao.com:3000",
  "pushgateway": "http://dev2.virnao.com:9091",
  "grafana_api_token": "Bearer eyJrIjoiMk9ZSmdkOWZOZk9zQmtBcDBKMHppQm5EVEZlNE1Dc3UiLCJuIjoiMDEvMTFfMDc6NDMiLCJpZCI6MX0=",
  "node": [
    {
      "name": "T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net",
      "type": "host",
      "arp": "on",
      "runtime": 610,
      "interface": [
        {
          "name": "enp129s0f1np1",
          "vlan": "not used",
          "ip": "10.251.87.82"
        },
        {
          "name": "T2_US_SDSC:sn3700_s0",
          "vlan": 3986,
          "peer": [
            {
              "name": None,
              "interface": None,
              "vlan": 3986
            }
          ]
        }
      ]
    },
    {
      "name": "T2_US_Caltech_Test:dellos9_s0",
      "type": "switch",
      "runtime": 610,
      "interface": [
        {
          "name": "hundredGigE_1-13",
          "vlan": 3986,
          "peer": [
            {
              "name": "aristaeos_s0",
              "interface": "Port-Channel501-rucio",
              "vlan": "not_used"
            }
          ]
        },
        {
          "name": "hundredGigE_1-10",
          "vlan": 3986,
          "peer": [
            {
              "name": None,
              "interface": None,
              "vlan": None
            }
          ]
        }
      ]
    },
    {
      "name": "T2_US_SDSC:sn3700_s0",
      "type": "switch",
      "runtime": 610,
      "interface": [
        {
          "name": "Ethernet80",
          "vlan": 3986,
          "peer": [
            {
              "name": "T2_US_SDSC:k8s-gen4-01.sdsc.optiputer.net",
              "interface": "enp129s0f1np1",
              "vlan": 3986
            }
          ]
        },
        {
          "name": "PortChannel501",
          "vlan": 3986,
          "peer": [
            {
              "name": "aristaeos_s0",
              "interface": "Port-Channel502",
              "vlan": "not_used"
            }
          ]
        }
      ]
    },
    {
      "name": "NRM_CENIC:aristaeos_s0",
      "type": "switch",
      "runtime": 610,
      "interface": [
        {
          "name": "Port-Channel501-rucio",
          "vlan": 3986,
          "peer": [
            {
              "name": "dellos9_s0",
              "interface": "hundredGigE_1-13",
              "vlan": "not_used"
            }
          ]
        },
        {
          "name": "Port-Channel502",
          "vlan": 3986,
          "peer": [
            {
              "name": "sn3700_s0",
              "interface": "PortChannel501",
              "vlan": "not_used"
            }
          ]
        }
      ]
    }
  ]
}

data, api = fill_API(data, 'admin', 'admin')