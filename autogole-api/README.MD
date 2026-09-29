# autogole-api

The RTMon package: the worker, its libraries, the Grafana templates, and the container packaging. See the
[repository README](../README.md) for what RTMon is, how it is configured, and how the image is built.

## How SENSE-O drives RTMon

RTMon exposes no control API to the orchestrator. Integration is by polling, and SENSE-O drives it through tasks.

1. A user enables monitoring on a service instance through the RTMon addon. SENSE-O creates a task under the configured
   assignee tag and delegates the instance to the account RTMon authenticates as.
2. Each cycle RTMon lists the tasks under that tag and keeps the ones whose deployment matches its own name.
3. For a kept task it fetches the manifest from SENSE-O, renders the dashboard, and reports the dashboard URL back on
   the task.
4. Per-instance options travel on the task, so they are chosen in the portal or in a service profile. RTMon advertises
   which options exist, with their defaults and limits, when it registers with the orchestrator.
5. On cancellation the dashboard is removed, or kept for the retention window the task asked for.

Because nothing is pushed to RTMon, an orchestrator that cannot be reached delays work rather than losing it. The
read-only API in `RTMonLibs/ResultsApi.py` is the only server RTMon runs. It serves cached SiteRM action results
outward to Grafana and accepts no instructions.

## Running outside a container

```sh
source dev-env.sh
pip3 install -r requirements.txt
pip3 install .
```

`dev-env.sh` puts `src/python` on `PYTHONPATH`. The worker needs `/etc/rtmon.yaml`, an auth file for each endpoint in
`sense_endpoints`, a Grafana API key, and the SiteRM client certificate before it will start. Templates are read from
`template_path`, which the image populates from `src/templates`.

The SENSE Python client is a separate repository. The Dockerfile installs it from source and `requirements.txt` does not
pin it, so a fix in the client reaches RTMon only when the image is rebuilt.
