#!/bin/bash

# Function to set up Grafana data source using its API
setup_data_source() {
    local api_url=$1
    local api_key=$2
    local datasource_name="$3"
    local prometheus_url=$4

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
        -d '$payload' \
        \"$api_url/api/datasources\""

    # Make POST request to Grafana API
    local response=$(curl -i -X POST \
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
# Function to create Grafana API key
create_grafana_api_key() {
    local grafana_domain=$(echo $1 | awk -F[/:] '{print $4}')
    local grafana_port=$(echo $1 | awk -F[/:] '{print $5}')
    local grafana_username=$2
    local grafana_password=$3
    local current_time=$(date +"%m/%d_%H:%M")
    local payload="{\"name\":\"$current_time\", \"role\": \"Admin\"}"
    echo "http://$grafana_username:$grafana_password@$grafana_domain:$grafana_port/api/auth/keys"
    # Make API call to create an API key
    local api_key_response=$(curl -s -X POST "http://$grafana_username:$grafana_password@$grafana_domain:$grafana_port/api/auth/keys" \
        -H "Content-Type: application/json" \
        -d "$payload")

    # Extract API key from the response
    local new_api_key=$(echo $api_key_response | grep -oP '"key":"\K[^"]+')
    echo "This is API KEY"
    echo $new_api_key
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
sleep 6
read -r -p "Config file [press enter for default choice config_cloud/config.yml]: " config_file

# Setting 'config_file' to its own value if it's already set, else setting it to 'config.yml' as a default.
config_file=${config_file:-config.yml}
# Using the variable 'config_file' in the echo statement.
echo "!!    Parsing ${config_file}"

# Running 'prometheus.py' with 'config_file' as an argument.
python3 prometheus.py ${config_file}

# Transporting Script Exporter configuration files
echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples




# Docker stack deployment
echo "!!    docker stack deployment"
docker stack deploy -c docker-stack.yml cloud
sleep 6
echo "Wait 1 minute while we setup the Data Source"
sleep 120

# Extract needed variables from config file
grafana_domain=$(grep grafana_public_domain "$config_file" | awk '{print $2}' | tr -d '"')
grafana_username=$(grep grafana_username "$config_file" | awk '{print $2}' | tr -d '"')
grafana_password=$(grep grafana_password "$config_file" | awk '{print $2}' | tr -d '"')

# Create Grafana API key
grafana_api_token=$(create_grafana_api_key $grafana_domain $grafana_username $grafana_password)
echo "!! Grafana API Key: $grafana_api_token"

# Set up data source with new API key
setup_data_source $grafana_domain $grafana_api_token "Prometheus" $prometheus_url

# Sleep command to allow for any necessary delays.
sleep 1



