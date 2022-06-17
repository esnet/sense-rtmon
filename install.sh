echo "!!    Initialize Docker Swarm"
MYIP=$(hostname -I | head -n1 | awk '{print $1;}')
echo "$MYIP is used for docker swarm advertise"
docker swarm init --advertise-addr $MYIP