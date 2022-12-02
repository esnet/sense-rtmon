# Kubernetes 
## Configuration Files

### Docker Conversion
- kompose used to convert Docker Compose file to Kubernetes files https://kompose.io
- Command used: `kompose convert -f docker-compose.yml`

### UCSD Deployment
- Gain Access: https://ucsd-prp.gitlab.io/userdocs/start/quickstart/
- When the correct `config` file is stored correctly, run container: `kubectl apply -f .`