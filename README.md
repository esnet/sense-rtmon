# sense-rtmon

RTMon generates Grafana dashboards for the network services provisioned by the SENSE Orchestrator. It polls SENSE-O for
tasks assigned to it, fetches the manifest of each service instance, and renders one dashboard per instance covering the
whole provisioned path rather than one site at a time.

RTMon measures nothing of its own. Panels are assembled from what each domain already publishes: the per-site Prometheus
exporters, the SiteRM frontend of each site on the path, and the manifest.

## Layout

| Path | Contents |
| --- | --- |
| `autogole-api/src/python/RTMon/worker.py` | The main loop: task polling, dashboard lifecycle, retention, retirement |
| `autogole-api/src/python/RTMonLibs/` | SENSE-O, SiteRM, Grafana and Prometheus clients, template rendering, warnings |
| `autogole-api/src/templates/` | Exported Grafana panel and dashboard JSON, with `REPLACEME` placeholders |
| `autogole-api/packaging/` | Dockerfile, the three entry points, and the default `/etc` files |
| `standarts/` | pylint and codespell configuration, used by CI and by `linter.sh` |
| `test/` | Standalone diagram and topology fixtures |

## Processes

`setup.py` installs three entry points. In the container all three come from one image, started under supervisord.

| Entry point | Role |
| --- | --- |
| `RTMon-Daemon` | The worker. One cycle every `sleep_timer` seconds |
| `RTMon-Http` | Read-only API serving the cached SiteRM action results, for the Grafana Infinity datasource. Off unless `http_api_enabled` is true |
| `RTMon-Health` | Kubernetes probe. `--mode liveness` reports whether cycles still complete, `--mode readiness` whether every orchestrator is reachable |

The two probe modes are deliberately separate. A remote outage marks the pod NotReady without restarting it, because a
restart cannot fix someone else's frontend.

## Configuration

One file, `/etc/rtmon.yaml`. The defaults live in `autogole-api/packaging/files/etc/rtmon.yaml`, which documents every
key. In a cluster the file is mounted from a Secret, so a new key added here does nothing until the Secret carries it.

Keys worth reading before a first deployment:

| Key | Why |
| --- | --- |
| `grafana_folder`, `grafana_dev` | Together they form the deployment name, and that one string is the Grafana folder, the name RTMon registers with SENSE-O, and the task filter. Setting `grafana_dev` therefore isolates an instance completely |
| `senseo_assignee` | The tag RTMon asks SENSE-O for tasks under. It must match the orchestrator's RTMon addon. A tag SENSE-O does not know returns an empty list rather than an error, so a typo looks like having no work |
| `sense_endpoints` | Each orchestrator and its auth file |
| `template_tag` | Written onto every dashboard. Bumping it rebuilds all of them in place |
| `hostcert`, `hostkey` | Client certificate for SiteRM. It has to be authorized by every frontend on the path |
| `siterm_actions_enabled` | Debug actions submitted straight to a SiteRM. When false they are advertised to SENSE-O as `(temporarily off)`, rather than accepting a test that never runs |

## Building

The Dockerfile clones the source from GitHub rather than copying the build context, so a change has to be pushed before
an image can contain it.

```sh
cd autogole-api/packaging
./build.sh
```

`build.sh` builds `linux/amd64` with no cache. Add `--build-arg RTMON_BRANCH=<branch>` to build something other than
`master`.

`docker-hub-upload.sh` pushes `<tag>-<date>` and then the moving `<tag>`, defaulting to `dev`. Production pulls `:dev`
with `imagePullPolicy: Always`, so a test image should be pushed under a dated tag directly instead of through this
script.

`packaging/start-dev.sh` runs the built image locally with the repository, the config files and the certificates bind
mounted. Deployment manifests are not in this repository.

## Linting

`./linter.sh` runs pylint, isort, pyink and yamllint over the files in `git diff`, using this repository's own pylint
configuration. CI runs super-linter with `VALIDATE_ALL_CODEBASE: false`, so it checks only the files a change touches.
An untouched file with existing findings stays green until something edits it.
