# Kubernetes Configuration Files

- `Docker Conversion`:
- kompose used to convert Docker Compose file to Kubernetes files https://kompose.io
- Command used: `kompose convert -f docker-compose.yml` under the parent directory
- After conversion, set `hostNetwork: true` under `spec` and above `containers` line in `deployment.yaml` file 

- `UCSD Deployment`:
- Gain Access: https://ucsd-prp.gitlab.io/userdocs/start/quickstart/
- When the `config` file is stored correctly, deployment : `kubectl apply -f .`