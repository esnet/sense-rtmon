#!/bin/bash

# Function to set up Grafana data source using its API
setup_data_source() {
    local api_url="$1"
    local api_key="$2"
    local datasource_name="$3"
    local prometheus_url="$4"

    # Create JSON payload for data source
    local payload=$(cat <<EOF
{
  "name": "$datasource_name",
  "type": "prometheus",
  "url": "$prometheus_url",
  "access": "proxy",
  "basicAuth": false
}
EOF
)

    # Make POST request to Grafana API
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $api_key" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$api_url/api/datasources")

    # Check response for success
    if [[ "$response" =~ "datasource created" ]]; then
        echo "Data source setup successful!"
    else
        echo "Error setting up data source: $response"
    fi
}

# Function to check if a port is in use
check_port() {
    local port=$1
    local is_in_use=$(sudo lsof -i -P -n | grep $port)

    if [ -z "$is_in_use" ]; then
        echo "Port $port is free"
    else
        echo "Port $port is in use"
    fi
}

# Display port status
echo "!!    Make sure Port 3000, 9090, 9091, 9469 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 3000"
check_port 3000
echo "!!    Check Port 9090"
check_port 9090
echo "!!    Check Port 9091"
check_port 9091
echo "!!    Check Port 9469"
check_port 9469

# Wait for user input for config file
sleep 2
read -r -p "Config file [press enter for default choice config_cloud/config.yml]: " config_file

# Setting 'config_file' to its own value if it's already set, else setting it to 'config.yml' as a default.
config_file=${config_file:-config.yml}

# Using the variable 'config_file' in the echo statement.
echo "!!    Parsing ${config_file}"

# Extract API key from config file
grafana_api_key=$(yq r "$config_file" grafana_api_key)

# Running 'prometheus.py' with 'config_file' as an argument.
python3 prometheus.py ${config_file}

# Sleep command to allow for any necessary delays.
sleep 1

# Transporting Script Exporter configuration files
echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1

# Docker stack deployment
echo "!!    docker stack deployment"
docker stack deploy -c docker-stack.yml cloud
sleep 3
