import json
import os
import sys
import re
import yaml
import requests
import base64
from datetime import datetime

# Function to create a service account
def create_service_account(grafana_base_url, admin_username, admin_password):
    url = f"{grafana_base_url}/api/serviceaccounts"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{admin_username}:{admin_password}'.encode()).decode()}"
    }
    data = {
        "name": "grafana",
        "role": "Admin",
        "isDisabled": False
    }
    print("Raw request for creating service account:")
    print(f"POST {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print("Response from creating service account:")
    print(response.text)
    if response_data.get('id'):
        return response_data.get('id')
    else:
        return None

# Function to generate a token for a service account
def generate_service_account_token(grafana_base_url, admin_username, admin_password, service_account_id):
    url = f"{grafana_base_url}/api/serviceaccounts/{service_account_id}/tokens"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{admin_username}:{admin_password}'.encode()).decode()}"
    }
    data = {
        "name": "sa-1-grafana"  # Use the same name as the service account
    }
    print("Raw request for generating token:")
    print(f"POST {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print("Response from generating token:")
    print(response.text)
    if response_data.get('key'):
        return response_data.get('key')
    else:
        return None

# get time for API keys
now = datetime.now()
current_time = now.strftime("%m/%d_%H:%M")    

# read yml file
with open(sys.argv[1], 'r') as stream:
    # Parse YAML data
    data = yaml.safe_load(stream)

# Create service account
service_account_id = create_service_account(data['grafana_public_domain'], data['grafana_username'], data['grafana_password'])
print("Service account ID:", service_account_id)

# Generate token for service account
api_key = generate_service_account_token(data['grafana_public_domain'], data['grafana_username'], data['grafana_password'], service_account_id)

if api_key:
    # Update YAML file with the generated token
    data['grafana_api_token'] = api_key
    with open(sys.argv[1], 'w') as file:
        yaml.dump(data, file)

    print(f"\nAPI Key: Bearer {api_key}")
    print("!!   API TOKEN GENERATION COMPLETE")