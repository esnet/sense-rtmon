#!/bin/bash

# Function to set up Grafana data source using its API
setup_data_source() {
    local api_url=$1
    local api_key=$2
    local datasource_name="$3"
    local prometheus_url=$4
    local max_retries=5
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if [ -z "$api_key" ]; then
            echo "!! Grafana API key is empty. Cannot proceed with data source setup !!"
            exit 1
        fi

        # Create JSON payload for data source
        local payload='{"name": "'"$datasource_name"'", "type": "prometheus", "url": "'"$prometheus_url"'", "access": "proxy", "basicAuth": false }'

        echo "!! Executing curl command to setup datasource !!"
        echo "curl -i -X POST \
            -H \"Authorization: Bearer $api_key\" \
            -H \"Content-Type: application/json\" \
            -H \"Accept: application/json\" \
            -d '$payload' \
            \"$api_url/api/datasources\""

        # Make POST request to Grafana API
        local response=$(curl -i -X POST \
            -H "Authorization: Bearer $api_key" \
            -H "Content-Type: application/json" \
            -H \"Accept: application/json\" \
            -d "$payload" \
            "$api_url/api/datasources")

        # Check response for success
        if [[ "$response" =~ "datasource created" ]]; then
            echo "Data source setup successful!"
            return 0
        else
            echo "Error setting up data source: $response"
            ((retry_count++))
            echo "Retrying ($retry_count/$max_retries)..."
            sleep 5  # Wait for 5 seconds before retrying
        fi
    done

    echo "Maximum retries reached. Unable to set up data source."
    exit 1
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
grafana_api_url=$(grep grafana_public_domain "$config_file" | awk '{print $2}' | tr -d '"')
grafana_api_token=$(grep grafana_api_token "$config_file" | awk '{print $2}' | tr -d '"')
prometheus_url=$(grep prometheus_url "$config_file" | awk '{print $2}' | tr -d '"')

# Sleep command to allow for any necessary delays.
sleep 1

# Running 'prometheus.py' with 'config_file' as an argument.
python3 prometheus.py ${config_file}

# Transporting Script Exporter configuration files
echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1

# Docker stack deployment
echo "!!    docker stack deployment"
docker stack deploy -c docker-stack.yml cloud
sleep 20
echo "!!    Setting up containers..."


python sa.py ${config_file}
sleep 5

grafana_api_url=$(grep grafana_public_domain "$config_file" | awk '{print $2}' | tr -d '"')
grafana_api_token=$(grep grafana_api_token "$config_file" | awk '{print $2}' | tr -d '"')
prometheus_url=$(grep prometheus_url "$config_file" | awk '{print $2}' | tr -d '"')
setup_data_source $grafana_api_url $grafana_api_token "Prometheus" $prometheus_url
