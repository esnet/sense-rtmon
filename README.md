# sense-rtmon

RTMon generates Grafana dashboards for the network services provisioned by the SENSE Orchestrator. It polls SENSE-O for
tasks assigned to it, fetches the manifest of each service instance, and renders one dashboard per instance covering the
whole provisioned path rather than one site at a time.

RTMon measures nothing of its own. Panels are assembled from what each domain already publishes: the per-site Prometheus
exporters, the SiteRM frontend of each site on the path, and the manifest.

## Layout

| Path                                      | Contents                                                                      |
| ----------------------------------------- | ----------------------------------------------------------------------------- |
| `autogole-api/src/python/RTMon/worker.py` | The main loop: task polling, dashboard lifecycle, retention, retirement       |
| `autogole-api/src/python/RTMonLibs/`      | SENSE-O, SiteRM, Grafana and Prometheus clients, template rendering, warnings |
| `autogole-api/src/templates/`             | Exported Grafana panel and dashboard JSON, with `REPLACEME` placeholders      |
| `autogole-api/packaging/`                 | Dockerfile, the three entry points, and the default `/etc` files              |
| `archify-sidecar/`                        | The Archify render/serve sidecar: its own image, `ghcr.io/esnet/rtmon`        |
| `standarts/`                              | pylint and codespell configuration, used by CI and by `linter.sh`             |
| `test/`                                   | Standalone diagram and topology fixtures                                      |

## Processes

`setup.py` installs three entry points. In the container all three come from one image, started under supervisord.

| Entry point    | Role                                                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `RTMon-Daemon` | The worker. One cycle every `sleep_timer` seconds                                                                                     |
| `RTMon-Http`   | Read-only API serving the cached SiteRM action results, for the Grafana Infinity datasource. Off unless `http_api_enabled` is true    |
| `RTMon-Health` | Kubernetes probe. `--mode liveness` reports whether cycles still complete, `--mode readiness` whether every orchestrator is reachable |

The two probe modes are deliberately separate. A remote outage marks the pod NotReady without restarting it, because a
restart cannot fix someone else's frontend.

## Configuration

One file, `/etc/rtmon.yaml`. The defaults live in `autogole-api/packaging/files/etc/rtmon.yaml`, which documents every
key. In a cluster the file is mounted from a Secret, so a new key added here does nothing until the Secret carries it.

Keys worth reading before a first deployment:

| Key                             | Why                                                                                                                                                                                                            |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `grafana_folder`, `grafana_dev` | Together they form the deployment name, and that one string is the Grafana folder, the name RTMon registers with SENSE-O, and the task filter. Setting `grafana_dev` therefore isolates an instance completely |
| `senseo_assignee`               | The tag RTMon asks SENSE-O for tasks under. It must match the orchestrator's RTMon addon. A tag SENSE-O does not know returns an empty list rather than an error, so a typo looks like having no work          |
| `sense_endpoints`               | Each orchestrator and its auth file                                                                                                                                                                            |
| `template_tag`                  | Written onto every dashboard. Bumping it rebuilds all of them in place                                                                                                                                         |
| `hostcert`, `hostkey`           | Client certificate for SiteRM. It has to be authorized by every frontend on the path                                                                                                                           |
| `siterm_actions_enabled`        | Debug actions submitted straight to a SiteRM. When false they are advertised to SENSE-O as `(temporarily off)`, rather than accepting a test that never runs                                                   |

## Topology diagrams

Every dashboard opens with a topology view of the provisioned path. `topdiagrams` in `rtmon.yaml` selects which of the
two are drawn — `Mermaid`, `Archify`, or `Both`.

|             |                                                                                                                              |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Mermaid** | The complete graph: every port, VLAN, address and BGP peer. Rendered inline by the `jdbranham-diagram-panel` plugin          |
| **Archify** | The same path at device level, with that detail moved into cards beside it, and interactive — focus views, trace, PNG export |

They answer different questions, so neither replaces the other. Whatever `topdiagrams` is set to, **the Mermaid walk
always runs**: `findorder()` consumes `manifest["Ports"]` as it goes, so there is exactly one walk available, and it is
what fills `orderlist`. Archify draws from the model that walk leaves behind rather than taking a second one, which is
also why the two panels cannot disagree about the topology.

Archify is **opt-in and off by default.** The renderer is not in the RTMon image: it runs in a sidecar container that
RTMon is only an HTTP client of. Uncommenting the `archify` block in `rtmon.yaml` and deploying a sidecar is what turns
it on. Until then RTMon draws Mermaid and says nothing — an install that has never been pointed at a sidecar is not a
misconfigured one.

The sidecar's source is `archify-sidecar/` in this repository and its image is `ghcr.io/esnet/rtmon`, built by
`.github/workflows/archify-image.yaml`. Two images out of one repository, deliberately: the sidecar is a Node runtime
plus a vendored Archify render tree, and folding that into the RTMon image would put both in every RTMon deployment
whether or not the operator draws this panel. As a separate image the cost falls only on deployments that opt in, and
nothing in the RTMon image changes for anyone else.

It is a second container in the RTMon pod rather than its own deployment, so `archify.sidecar_url` is a loopback
address — containers in one pod share a network namespace. That is also why the sidecar listens on 8081: `http_api_port`
above defaults to 8080 and the two cannot both have it.

`archify-sidecar/archify-cli/` is vendored upstream Archify, pinned by its own `VERSION`, and is excluded from
super-linter through `FILTER_REGEX_EXCLUDE` and from Biome through `biome.json` — Biome is handed the whole workspace
and never sees the former. Reformatting code this repository does not own would turn the next version bump into a
merge conflict. `THIRD_PARTY_NOTICES.md` beside it records the licences (Archify MIT, JetBrains Mono under the OFL).
Upstream's generated brand-mark tree is deliberately emptied rather than vendored.

### The sidecar contract

RTMon depends on this interface, not on any particular implementation. Three endpoints, and only the first two are
needed to render a dashboard:

|                                                        |                                                                                                    |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `POST /v1/render`                                      | `{uid, ir, quality}` with `Authorization: Bearer <archify.token>`. Renders and stores the artifact |
| `GET /diagrams/<uid>.html`                             | What the panel's iframe fetches. Public, read-only — it carries no secret                          |
| `POST /api/v1/sweep`, `DELETE /api/v1/artifacts/<uid>` | Teardown, so artifacts do not outlive their dashboards                                             |

`ir` is the Archify architecture IR built by `RTMonLibs/ArchifyIR.py`, which is a pure function of the path model and is
covered by `test/test_archify.py` without any sidecar running. Anything that accepts that IR and serves the result at
that URL will work.

The implementation that ships with this is `archify-sidecar/`, and `archify-sidecar/test/server.test.mjs` checks it
against that contract with `node --test`. Writing another implementation of the three endpoints above and pointing
`archify.sidecar_url` at it is equally valid — RTMon never learns which one answered.

Being _half_-configured is different and is reported on the dashboard, because setting one of `archify.sidecar_url` and
`archify.diagram_url_base` and not the other is someone who meant to turn this on. So is `topdiagrams: Archify` with no
sidecar configured, which would otherwise leave a dashboard with no topology diagram and no reason given.

Nothing about this is allowed to fail a dashboard. A sidecar that is down, a renderer that rejects the layout, a render
that hangs — each ends the same way, with a line in the dashboard's own _Graph Generation Warnings_ row and no Archify
panel. The Mermaid panel is right there and still complete.

Grafana must set `disable_sanitize_html = true` (or `GF_PANELS_DISABLE_SANITIZE_HTML=true`) for the panel's iframe to
survive; without it the panel renders empty.

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

The Archify sidecar is a second image from the same repository and is built from the checkout rather than a clone, so
it needs no branch argument:

```sh
cd archify-sidecar
node --test test/server.test.mjs
docker build . --tag ghcr.io/esnet/rtmon:archify-dev
```

In CI that is `.github/workflows/archify-image.yaml`, which runs those tests, builds, and pushes `<tag>-<date>` then
the moving `<tag>` to `ghcr.io/esnet/rtmon` using the job's own `GITHUB_TOKEN`. It only fires for changes under
`archify-sidecar/`, because nothing else in this repository can change that image.

## Linting

`./linter.sh` runs pylint, isort, pyink and yamllint over the files in `git diff`, using this repository's own pylint
configuration. CI runs super-linter with `VALIDATE_ALL_CODEBASE: false`, so it checks only the files a change touches.
An untouched file with existing findings stays green until something edits it.
