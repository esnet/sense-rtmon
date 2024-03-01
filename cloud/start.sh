#! /bin/bash

echo "!!    Make sure Port 3000, 9090, 9091, 9469 are not in use"
echo "!!    sudo lsof -i -P -n | grep LISTEN"
echo "!!    Check Port 3000"
sudo lsof -i -P -n | grep 3000
echo "!!    Check Port 9090"
sudo lsof -i -P -n | grep 9090
echo "!!    Check Port 9091"
sudo lsof -i -P -n | grep 9091
echo "!!    Check Port 9469"
sudo lsof -i -P -n | grep 9469

sleep 2
read -r -p "Config file [press enter for default choice config_cloud/config.yml]: " config_file



# Setting 'config_file' to its own value if it's already set, else setting it to 'config.yml' as a default.
# This helps by ensuring that 'config_file' is always set to a useful value, eliminating the need for a conditional check later on.
config_file=${config_file:-config.yml}

# Using the variable 'config_file' in the echo statement. Because of the previous line, we know 'config_file' is always set here.
# So we've simplified the code by eliminating an 'if' statement, making it more readable and less error-prone.
echo "!!    Parsing ${config_file}"

# Running 'prometheus.py' with 'config_file' as an argument. Again, we know 'config_file' is set due to the previous line.
# This simplifies the code, as we only need one line to run 'prometheus.py', regardless of whether 'config_file' was initially set or not.
python3 prometheus.py ${config_file}

# Sleep command to allow for any necessary delays, unchanged from the original code.
sleep 1

# echo "!!    Transporting Script Exporter configuration files"
yes | cp -rfa se_config/. script_exporter/examples
sleep 1

echo "!!    docker stack deployment"
docker stack deploy -c docker-stack.yml cloud

sleep 3

echo "!!    IMPORTANT:"
echo "!!    Before Generating Dashboard for the first time please setup Data Source and Grafana authorization API key"
echo "!!    API key can be done automatically but Data Source needs to be configured MANUALLY:"
echo "!!    Visit Google Doc for Grafana API and add Prometheus as a Data Source "
echo "!!    Instruction: https://docs.google.com/document/d/e/2PACX-1vRAwtpqlMKbii-hiqMoFD_N5PghMSw2eTMts9VhBww3AoSnXnQkjEcra4ReyLLsXrAuE_VEwLHRg33c/pub"
sleep 3

echo ""
echo ""
echo "!!    Wait for 3-5 seconds for the containers to get started"
echo "!!    Visit grafana through its port (default 3000)"
echo "- navigate to http://<ip_address/domain_name>:3000 (or https://<ip_address/domain_name> if HTTPS enabled and port 443 enabled)"
echo "- login to Grafana with the default authentication (username: admin, password: admin)"
sleep 2
echo ""
echo "!!    APT Key setup instruction (used for dynamic flow dashboard. ignore if API key already set up):"
sleep 2
echo "- setting -> API keys -> add key with Admin permission"
echo "- copy the API token value starting with 'Bearer ....'"
echo "- edit any files under /config_flow that are used"
echo "- replace 'CONFIG' in {grafanaAPIToken: 'CONFIG'} with the new API token"
sleep 2
echo ""
echo "!!    Data source setup instruction:"
sleep 2
echo "- navigate to <ip_address/domain_name>:3000(or 443 if HTTPS enabled)"
echo "- login to Grafana with the default authentication (username: admin, password: admin)"
echo "- setting -> data source -> Prometheus -> URL -> Save & Test"
echo "- enter the IP address NOT DNS"
sleep 5
CONFIG_YAML="../config_cloud/config.yml"

# Extract paths using grep and cut
PRIVATECERT_PATH=$(grep 'privatecert:' $CONFIG_YAML | cut -d ' ' -f 2 | tr -d '\n' | tr -d "'")
CERT_PATH=$(grep 'certkey:' $CONFIG_YAML | cut -d ' ' -f 2 | tr -d '\n' | tr -d "'")



# Create the update.sh file
cat <<EOF > update1.sh
#!/bin/bash

# Copy files to current directory
cp "${PRIVATECERT_PATH}" .
cp "${CERT_PATH}" .
cp /root/.sense-o-auth.yaml .
cp ../config_cloud/config.yml .
cp -r ../config_flow .

# Build the Docker container with network host and interactive mode
docker build --network host -t mainloop .

# Run the Docker container in interactive mode
docker run -itd mainloop

# Remove the copied files
rm privkey.pem cert.pem .sense-o-auth.yaml config.yml
rm -r config_flow
EOF

# Make the script executable
chmod +x update1.sh
./update1.sh
# echo ""
# echo "!!    What's next?"
# echo "!!    Generate flow dashboard: run python3 main.py  to generate a dashboard based on the configuration files under config_flow"
# echo "!!    Delete the deployment: run ./clean.sh to remove cloud stack"
