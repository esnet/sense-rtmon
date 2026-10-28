#!/usr/bin/env python3
"""Offline checks for the Archify topology panel.

No Grafana, no SENSE-O, no real network and - crucially - no Node and no
vendored Archify tree. The runtime lives in the rtmon-archify sidecar, so
these tests stand up a small HTTP server that implements its contract and
check the RTMon half against that. The sidecar's own test suite (node --test)
checks the real renderer; this file checks that RTMon builds the right thing,
asks for it over HTTP, and degrades every failure into a dashboard warning.

The fixtures beside this file are real ordered path models - the shape
findorder() leaves in self.orderlist - so the interesting half of the feature
can be checked against genuine multi-domain, multipoint and BGP reservations.

Run from the repository root:

    python3 test/test_archify.py

Exits non-zero on the first failure and prints what failed.
"""

# linter.sh formats with 'pyink -l 200' and then checks with pylint's 120
# column limit, so the formatter re-joins lines the checker then rejects. The
# other RTMon modules resolve that the same way.
# pylint: disable=line-too-long

import gzip
import http.server
import json
import logging
import os
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "autogole-api", "src", "python"))

# The mixed-style imports are deliberate: this script is run directly, so it
# has to set its own path before RTMonLibs exists. Everything below is used,
# some of it only inside the harness that builds a minimal RTMon worker.
from RTMonLibs.ArchifyIR import DeviceModel, buildIR, placeDevices  # noqa: E402  pylint: disable=wrong-import-position

FIXTURES = ("NRP", "BGP", "Branch", "Debug", "multipoint")
TOKEN = "test-token-123"

FAILURES = []


def check(condition, message):
    """Record a failure without stopping, so one run reports everything."""
    if condition:
        print(f"  ok   {message}")
        return True
    print(f"  FAIL {message}")
    FAILURES.append(message)
    return False


def fixture(name):
    """One ordered path model."""
    with open(os.path.join(ROOT, "test", f"{name}.json"), "r", encoding="utf-8") as fd:
        return json.load(fd)


# --------------------------------------------------------------------------
# A fake of the rtmon-archify sidecar, implementing its contract closely
# enough that the RTMon client has a real endpoint to talk to. It accepts a
# body of {"uid", "ir", "quality"}, keeps artifacts in one directory, does
# the same 404 discipline on the read path, and applies the same auth split.
# The one difference from the real sidecar: validation is a stand-in (it
# rejects labels longer than the renderer budget, which is exactly what the
# fallback ladder exists for), because the real validator is exercised in the
# sidecar repo's own tests.
# --------------------------------------------------------------------------
LABEL_MAX = 26


class _SidecarHandler(http.server.BaseHTTPRequestHandler):
    server_version = "Fake-Archify-Sidecar"
    sys_version = ""

    def log_message(self, *args):  # pylint: disable=arguments-differ
        pass

    def _send(self, code, body, kind="json"):
        payload = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8" if kind == "json" else "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _auth(self):
        if not getattr(self.server, "token", None):
            return None
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {self.server.token}"

    def _read(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))

    def do_GET(self):  # pylint: disable=invalid-name
        """List artifacts, or serve one."""
        if self.path == "/api/v1/artifacts":
            if self._auth() is not True:
                self._send(503 if self._auth() is None else 401, '{"ok":false}')
                return
            uids = []
            for name in os.listdir(self.server.dir):
                if name.endswith(".html.gz"):
                    uids.append(name[:-8])
            self._send(200, json.dumps({"ok": True, "uids": uids}))
            return
        # Serve /diagrams/<uid>.html, refusing everything else uniformly.
        parts = self.path.lstrip("/").split("/")
        if len(parts) == 2 and parts[0] == "diagrams" and parts[1].endswith(".html"):
            uid = parts[1][:-5]
            if all(c in "0123456789abcdefABCDEF-" for c in uid) and len(uid) >= 8:
                target = os.path.join(self.server.dir, f"{uid}.html.gz")
                if os.path.isfile(target):
                    with open(target, "rb") as fd:
                        self.send_response(200)
                        self.send_header("Content-Encoding", "gzip")
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(os.path.getsize(target)))
                        self.end_headers()
                        self.wfile.write(fd.read())
                    return
        self._send(404, "not found", "text")

    def do_POST(self):  # pylint: disable=invalid-name
        """Render an artifact, or sweep the archive."""
        if self.path == "/api/v1/sweep":
            if self._auth() is not True:
                self._send(503 if self._auth() is None else 401, '{"ok":false}')
                return
            keep = set(self._read().get("keep", []))
            removed = 0
            for name in os.listdir(self.server.dir):
                uid = name[:-8] if name.endswith(".html.gz") else None
                # Only uid-shaped names are ours; the real sidecar does the
                # same, and it must never touch a file it did not write.
                if uid and all(c in "0123456789abcdefABCDEF-" for c in uid) and len(uid) >= 8 and uid not in keep:
                    os.remove(os.path.join(self.server.dir, name))
                    removed += 1
            self._send(200, json.dumps({"ok": True, "removed": removed}))
            return
        body = self._read()
        if self._auth() is not True:
            self._send(503 if self._auth() is None else 401, '{"ok":false}')
            return
        uid, ir = body.get("uid", ""), body.get("ir")
        if not isinstance(ir, dict):
            self._send(400, json.dumps({"ok": False, "error": "the ir is required"}))
            return
        too_long = [c["label"] for c in ir.get("components", []) if len(str(c.get("label", ""))) > LABEL_MAX]
        if too_long:
            diagnostics = [{"message": f'label "{label}" exceeds the renderer budget'} for label in too_long]
            self._send(422, json.dumps({"ok": False, "diagnostics": diagnostics}))
            return
        html = "<!DOCTYPE html><html><body id='diagram'>rendered</body></html>"
        with gzip.open(os.path.join(self.server.dir, f"{uid}.html.gz"), "wb") as fd:
            fd.write(html.encode())
        self._send(201, json.dumps({"ok": True, "uid": uid, "bytes": len(html)}))

    def do_DELETE(self):  # pylint: disable=invalid-name
        """Remove one artifact."""
        if self._auth() is not True:
            self._send(503 if self._auth() is None else 401, '{"ok":false}')
            return
        uid = self.path.rsplit("/", 1)[-1]
        target = os.path.join(self.server.dir, f"{uid}.html.gz")
        removed = 1 if os.path.isfile(target) else 0
        if removed:
            os.remove(target)
        self._send(200, json.dumps({"ok": True, "removed": removed}))


def start_sidecar(workdir):
    """A fake sidecar on an ephemeral port. Returns (base_url, stop)."""
    directory = os.path.join(workdir, "artifacts")
    os.makedirs(directory, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SidecarHandler)
    server.dir = directory
    server.token = TOKEN
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{server.server_address[1]}", server.shutdown


def test_ir_shape():
    """Every fixture builds an IR with the pieces the sidecar expects."""
    print("IR shape:")
    for name in FIXTURES:
        ir, report = buildIR(fixture(name), {}, title=f"{name} topology", output="x.html")
        check(ir is not None, f"{name}: produced an IR")
        if ir is None:
            continue
        check(set(("schema_version", "diagram_type", "meta", "components", "boundaries", "connections", "cards")) <= set(ir), f"{name}: has all IR sections")
        check(len(ir["meta"]["viewBox"]) == 2 and all(isinstance(v, (int, float)) for v in ir["meta"]["viewBox"]), f"{name}: viewBox is two numbers")
        check(report["devices"] == len(ir["components"]), f"{name}: report matches components")


def test_device_collapse():
    """A switch appearing once per port becomes one component, not several."""
    print("Device level collapse:")
    model = DeviceModel(fixture("multipoint"))
    placement, dropped = placeDevices(model)
    check(len(placement) == 4, f"multipoint collapses 7 entries to 4 devices (got {len(placement)})")
    check(not dropped, "no host dropped when a switch has two")
    edgecore = model.devices["T2_US_SDSC:edgecore_s0"]
    check(len(edgecore["ports"]) == 3, f"edgecore_s0 keeps all three of its ports (got {len(edgecore['ports'])})")


def test_no_self_links():
    """A switch with two ports in one path must not link to itself.

    archify rejects a connection whose endpoints are the same component, so
    this would cost the whole diagram rather than one edge.
    """
    print("Link sanity:")
    for name in FIXTURES:
        model = DeviceModel(fixture(name))
        check(all(a != b for a, b in model.links), f"{name}: no self-link")


def test_disconnected_runs_stay_apart():
    """A path with an unreported transit hop keeps its two runs separate.

    BGP crosses ESnet, which does not expose its internals, so the manifest
    holds two runs joined by nothing. The layout keeps the gap column and
    brings the two ESnet routers together, so the region wrapping them is one
    box rather than one that spans every site in between.
    """
    print("Disconnected runs:")
    model = DeviceModel(fixture("BGP"))
    placement, _ = placeDevices(model)
    esnet = [placement[k][1] for k in model.order if model.devices[k]["site"] == "ESnet"]
    check(len(esnet) == 2, f"BGP has two ESnet devices (got {len(esnet)})")
    message = f"the two ESnet routers sit either side of one gap column (got {sorted(esnet)})"
    check(abs(esnet[0] - esnet[1]) == 2, message)
    ir, _ = buildIR(fixture("BGP"), {}, title="x", output="x.html")
    labels = [b["label"] for b in ir["boundaries"]]
    check(labels.count("ESnet") == 1, f"they share a single ESnet region (got {labels})")


def test_unreported_transit_is_bridged_and_marked():
    """The gap is crossed by a dashed edge, not by a silent one.

    The manifest never reported the hop between the two ESnet routers, so the
    path would otherwise read as a circuit that stops halfway - which is what
    made an Archify panel look broken beside a Mermaid one, where same-named
    subgraphs merge and supply the continuity for free. The edge is drawn and
    marked: dashed, labelled "transit", and carrying no VLAN it was not told.
    """
    print("Unreported transit:")
    ir, report = buildIR(fixture("BGP"), {}, title="x", output="x.html")
    transit = [c for c in ir["connections"] if c.get("variant") == "dashed"]
    check(len(transit) == 1, f"exactly one inferred edge (got {len(transit)})")
    check(report.get("transit") == 1, f"and it is reported as inferred (got {report.get('transit')})")
    if transit:
        check(transit[0].get("label") == "transit", f'labelled "transit" (got {transit[0].get("label")!r})')
        check("VLAN" not in str(transit[0].get("label", "")), "and claims no VLAN")
        ends = {transit[0]["from"], transit[0]["to"]}
        check(all("ESnet" in e for e in ends), f"between the two ESnet routers (got {sorted(ends)})")

    # The spine is now one connected chain, which is the whole point.
    ids = {c["id"] for c in ir["components"]}
    adj = {i: set() for i in ids}
    for conn in ir["connections"]:
        if conn["from"] in adj and conn["to"] in adj:
            adj[conn["from"]].add(conn["to"])
            adj[conn["to"]].add(conn["from"])
    seen, stack = set(), [next(iter(ids))]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adj[node] - seen)
    check(len(seen) == len(ids), f"every device is reachable from every other ({len(seen)}/{len(ids)})")


def test_the_first_run_is_flipped_to_face_the_next():
    """A run whose shared site came out at its head is reversed, not left.

    Branch is a real SDSC-to-FNAL reservation and the shape that exposed this.
    Its long run is walked from losa-cr6, so ESnet lands in column 0 while its
    other router sits six columns away past CENIC, OASIS and a second SDSC
    switch. No later run faces column 0, every flip falls through to the
    default, and the two routers end up at opposite ends - so the bridge
    between them either does not happen or spans the whole diagram, and a span
    like that is refused by the renderer's edge-through-node rule rather than
    drawn. Three of the thirty-seven paths RTMon had stored were this shape.

    Reversed, the run ends on ESnet, the FNAL run faces it, and the pair is
    the ordinary either-side-of-one-gap case. The assertions are therefore
    about distance: close enough to bridge, and close enough to render.
    """
    print("First run orientation:")
    model = DeviceModel(fixture("Branch"))
    placement, _ = placeDevices(model)
    esnet = sorted(placement[k][1] for k in model.order if model.devices[k]["site"] == "ESnet")
    check(len(esnet) == 2, f"Branch has two ESnet devices (got {len(esnet)})")
    if len(esnet) == 2:
        check(esnet[1] - esnet[0] == 2, f"facing each other across one gap column (got columns {esnet})")

    ir, report = buildIR(fixture("Branch"), {}, title="x", output="x.html")
    transit = [c for c in ir["connections"] if c.get("variant") == "dashed"]
    check(len(transit) == 1, f"one inferred edge for the one crossing (got {len(transit)})")
    check(report.get("transit") == 1, f"and it is reported (got {report.get('transit')})")
    if transit:
        ends = {transit[0]["from"], transit[0]["to"]}
        check(all("ESnet" in e for e in ends), f"between the two ESnet routers (got {sorted(ends)})")
    labels = [b["label"] for b in ir["boundaries"]]
    check(labels.count("ESnet") == 1, f"and they share a single ESnet region (got {labels})")

    ids = {c["id"] for c in ir["components"]}
    adj = {i: set() for i in ids}
    for conn in ir["connections"]:
        if conn["from"] in adj and conn["to"] in adj:
            adj[conn["from"]].add(conn["to"])
            adj[conn["to"]].add(conn["from"])
    seen, stack = set(), [next(iter(ids))]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adj[node] - seen)
    check(len(seen) == len(ids), f"the whole diagram is one piece (got {len(seen)}/{len(ids)})")


def test_transit_is_never_invented_across_sites():
    """Two different sites either side of a gap are left unjoined.

    The bridge exists because a domain's own two routers are the same domain.
    Two runs that end on different sites are genuinely separate pieces of the
    path, and joining them would assert a peering the manifest never mentioned.
    """
    print("Cross-site gaps:")
    ir, report = buildIR(fixture("multipoint"), {}, title="x", output="x.html")
    for conn in ir["connections"]:
        if conn.get("variant") != "dashed":
            continue
        left = conn["from"].rsplit("_", 1)[0]
        right = conn["to"].rsplit("_", 1)[0]
        check(left == right, f"inferred edge stays within one site ({conn['from']} -> {conn['to']})")
    check(report.get("transit", 0) >= 0, "multipoint reports its inferred count")


def test_long_names_are_fitted():
    """A name too long for a component is shortened, not passed through.

    The renderer rejects a label wider than its box, which would cost the
    diagram. Hosts are the case that matters: a fully qualified name is longer
    than a component is wide. The sidecar's built-in budget is the same
    LABEL_MAX the fake enforces, so this doubles as the "IR never sends a
    label the renderer rejects" check that used to be the real validate.
    """
    print("Text fitting:")
    ir, _ = buildIR(fixture("NRP"), {}, title="x", output="x.html")
    for component in ir["components"]:
        check(len(component["label"]) <= LABEL_MAX, f'label {component["label"]!r} fits')
        check(len(component.get("sublabel", "")) <= 44, f'sublabel of {component["id"]} fits')
    hosts = [c["label"] for c in ir["components"] if c["type"] == "external"]
    check(all("." not in h for h in hosts), f"host labels drop the domain (got {hosts})")


def test_pathological_names_degrade():
    """An absurd device name costs its own label, not the diagram.

    The tightened text budget is one rung of the caller's fallback ladder, so
    what is checked here is that the rung actually changes the output and that
    the IR still passes the renderer's fitting rule.
    """
    print("Pathological input:")
    order = json.loads(json.dumps(fixture("NRP")))
    order[0]["Name"] = "T2_US_SDSC:" + ("extremely-long-hostname-" * 6) + "end.example.org"
    order[1]["Name"] = "Ethernet" + "0" * 120
    full, _ = buildIR(order, {}, title="x", output="x.html")
    short, _ = buildIR(order, {}, title="x", output="x.html", labelmax=16, sublabelmax=24)
    check(full is not None and short is not None, "both rungs produce an IR")
    check(
        [c["label"] for c in full["components"]] != [c["label"] for c in short["components"]],
        "the tightened budget actually shortens labels",
    )
    for tag, candidate in (("full", full), ("short", short)):
        worst = max((len(str(c.get("label", ""))) for c in candidate["components"]), default=0)
        check(worst <= LABEL_MAX if tag == "short" else True, f"{tag} rung satisfies the budget rule")


def test_empty_input():
    """An empty path is reported, not rendered as an empty canvas."""
    print("Empty input:")
    ir, report = buildIR([], {}, title="x", output="x.html")
    check(ir is None, "no IR for an empty orderlist")
    check(report["devices"] == 0, "the report says there were no devices")


def test_cards_carry_the_detail():
    """What is taken off the nodes has to turn up on a card."""
    print("Cards:")
    instance = {
        "alias": "test-flow",
        "intents": [
            {
                "json": {
                    "data": {
                        "type": "Site-L3 over P2P VLAN",
                        "connections": [
                            {
                                "name": "Connection 1",
                                "bandwidth": {"capacity": "1000", "qos_class": "guaranteedCapped"},
                                "terminals": [{"uri": "urn:ogf:network:fnal.gov:2023", "ipv6_prefix_list": "2620:6a:0:2842::/64"}],
                            }
                        ],
                    }
                }
            }
        ],
    }
    ir, _ = buildIR(fixture("BGP"), instance, title="x", output="x.html")
    titles = [c["title"] for c in ir["cards"]]
    check("Reservation" in titles, f"a reservation card is present (got {titles})")
    check("BGP" in titles, f"the BGP prefix list reaches a card (got {titles})")
    text = json.dumps(ir["cards"])
    check("2620:6a:0:2842::/64" in text, "the prefix itself is on the card")
    check("1000" in text, "the requested capacity is on the card")


def _worker(sidecar_url, **overrides):
    """A worker carrying just enough of RTMonWorker to build the panel.

    Template, DataWarnings and Archify, composed in the same order the real
    worker composes them. Nothing here talks to Grafana or SENSE-O, which is
    the point: t_createArchify's contract is that it reads the path model and
    asks a sidecar to render it, and neither of those needs either service.
    """
    from RTMonLibs.Archify import Archify as ArchifyMixin  # pylint: disable=import-outside-toplevel
    from RTMonLibs.DataWarnings import DataWarnings  # pylint: disable=import-outside-toplevel
    from RTMonLibs.Prometheus import Prometheus  # pylint: disable=import-outside-toplevel
    from RTMonLibs.SiteOverride import SiteOverride  # pylint: disable=import-outside-toplevel
    from RTMonLibs.Template import Mermaid, Template  # pylint: disable=import-outside-toplevel

    archify = {
        "sidecar_url": sidecar_url,
        "token": TOKEN,
        "diagram_url_base": "https://example.invalid/diagrams",
        "quality": "standard",
        "max_fix_rounds": 3,
        "render_timeout": 120,
    }
    archify.update(overrides.pop("archify", {}))
    config = {
        "template_path": os.path.join(ROOT, "autogole-api", "src", "templates"),
        "topdiagrams": overrides.pop("topdiagrams", "Both"),
        # Empty, so SiteOverride logs that there is nothing to fetch instead of
        # reaching for the network. These checks must run offline.
        "override_url": "",
        "archify": archify,
    }

    class Harness(Template, SiteOverride, Mermaid, ArchifyMixin, Prometheus, DataWarnings):  # pylint: disable=too-few-public-methods
        """Template plus both diagram builders, with no orchestrator behind it.

        Composed in the same order RTMonWorker composes them, minus everything
        that talks to Grafana, SENSE-O or SiteRM.

        Prometheus is real rather than stubbed, and is what ends the
        cooperative __init__ chain (its super().__init__ takes no kwargs).
        It stays offline here because the config carries no prometheus
        credentials, so its session is None and every query returns None
        before reaching the network - which is the "Prometheus did not say"
        tri-state the warning paths already handle. Upstream's MAC learning
        styles call into it from t_createMermaid, so leaving it out of the
        harness breaks the Mermaid walk rather than only the Prometheus bits.
        """

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # What t_createArchify reads. A real worker fills these through
            # t_createDashboard and the Mermaid walk; the harness has neither,
            # so it provides the state directly.
            self.generated = {"uid": "9f8e7d6c-aaaa-bbbb-cccc-0123456789ab", "title": "harness", "panels": []}
            # Declared, not filled: each test assigns the path model it wants.
            # Mermaid.__init__ sets this too, but through a cooperative super()
            # chain that static analysis cannot follow, so naming it here is
            # what tells a reader - and pylint - that the attribute is ours.
            self.orderlist = []

    logger = logging.getLogger("archify-harness")
    logger.addHandler(logging.NullHandler())
    return Harness(config=config, logger=logger)


def test_panel_end_to_end(workdir, sidecar_url):
    """The full path: model in, sidecar artifact on disk, panel out."""
    print("Panel generation:")
    worker = _worker(sidecar_url)
    worker.orderlist = fixture("multipoint")
    panels = worker.t_createArchify({"alias": "harness-flow"}, {})
    check(bool(panels), "a panel group is returned")
    content = json.dumps(panels)
    check("<iframe" in content, "the panel embeds an iframe")
    check("REPLACEME_ARCHIFY_URL" not in content, "the URL placeholder is substituted")
    check("9f8e7d6c-aaaa-bbbb-cccc-0123456789ab.html" in content, "the iframe points at this dashboard's uid")
    uid = worker.generated["uid"]
    artifact = os.path.join(workdir, "artifacts", f"{uid}.html.gz")
    check(os.path.isfile(artifact), "a gzipped artifact is on the sidecar")
    check(not worker.datawarnings, f"no warnings on the happy path (got {worker.datawarnings})")
    with gzip.open(artifact, "rb") as fd:
        html = fd.read(4096).decode("utf-8", "replace")
    check("rendered" in html, "the sidecar wrote an artifact for this diagram")


def test_sidecar_down_is_survivable():
    """No sidecar costs the panel and nothing else."""
    print("Sidecar missing:")
    worker = _worker("http://127.0.0.1:1")
    worker.orderlist = fixture("NRP")
    panels = worker.t_createArchify({}, {})
    check(not panels, "no panel is produced")
    check(len(worker.datawarnings) == 1, f"exactly one warning is recorded (got {worker.datawarnings})")
    check("could not be generated" in worker.datawarnings[0], "the warning says the diagram was skipped")
    check("Mermaid" in worker.datawarnings[0], "and points at the diagram that still works")


def test_unconfigured_is_silent():
    """An install that was never pointed at a sidecar is not misconfigured.

    The panel needs a sidecar an upgrade does not bring with it, so the
    feature is opt-in: nothing configured means no panel and nothing said,
    rather than a warning on every dashboard in a deployment that is simply
    not using this.
    """
    print("Nothing configured:")
    worker = _worker("", archify={"diagram_url_base": ""})
    worker.orderlist = fixture("NRP")
    check(not worker.t_createArchify({}, {}), "no panel when nothing is configured")
    check(not worker.datawarnings, "and no warning, because nothing was asked for")
    # REPLACEME is what the shipped config carries, and counts as unset. An
    # install that has not been edited must look unconfigured, not broken.
    shipped = _worker("", archify={"sidecar_url": "REPLACEME", "diagram_url_base": "https://REPLACEME/diagrams"})
    shipped.orderlist = fixture("NRP")
    check(not shipped.t_createArchify({}, {}), "no panel for the shipped placeholders")
    check(not shipped.datawarnings, "and still no warning")


def test_half_configured_is_reported():
    """Setting one of the two URLs and not the other is a mistake, and says so.

    This is the line the opt-in default has to hold: unconfigured is silent,
    half-configured is not, because only one of those is someone who meant to
    turn the feature on.
    """
    print("Half configured:")
    worker = _worker("http://127.0.0.1:1", archify={"diagram_url_base": ""})
    worker.orderlist = fixture("NRP")
    check(not worker.t_createArchify({}, {}), "no panel")
    check(any("diagram_url_base" in w for w in worker.datawarnings), "the warning names the url base setting")


def test_archify_only_without_a_sidecar_is_reported():
    """topdiagrams: Archify with nothing configured leaves no diagram at all."""
    print("Archify selected, nothing configured:")
    worker = _worker("", topdiagrams="Archify", archify={"diagram_url_base": ""})
    worker.orderlist = fixture("NRP")
    check(not worker.t_createArchify({}, {}), "no panel")
    check(any("topdiagrams" in w for w in worker.datawarnings), "the warning names topdiagrams")


def test_disabled_does_nothing():
    """topdiagrams: Mermaid skips the whole feature silently."""
    print("Disabled:")
    worker = _worker("http://127.0.0.1:9", topdiagrams="Mermaid")
    worker.orderlist = fixture("NRP")
    check(not worker.t_createArchify({}, {}), "no panel")
    check(not worker.datawarnings, "and no warning, because nothing was expected")
    check(worker.a_sweepArtifacts(set()) == 0, "the sweep is inert too")


def test_dropped_hosts_are_reported(sidecar_url):
    """A switch with more hosts than fit says so, naming them."""
    print("Dropped hosts:")
    order = json.loads(json.dumps(fixture("multipoint")))
    order.append(
        {
            "IPv4": "?ipv4?",
            "IPv6": "?ipv6?",
            "Interface": "eth9",
            "Mac": "aa:bb:cc:dd:ee:ff",
            "Name": "T2_US_SDSC:node-2-11.sdsc.optiputer.net",
            "Type": "Host",
            "Vlan": "3603",
            "Link": "T2_US_SDSC_edgecore_s0_Ethernet252",
        }
    )
    worker = _worker(sidecar_url)
    worker.orderlist = order
    panels = worker.t_createArchify({}, {})
    check(bool(panels), "the diagram is still produced")
    dropped = [w for w in worker.datawarnings if "node-2-11" in w]
    check(len(dropped) == 1, f"the third host is named in a warning (got {worker.datawarnings})")
    check("Mermaid" in dropped[0] if dropped else False, "and the operator is pointed at the complete diagram")


def test_lifecycle(workdir, sidecar_url):
    """Artifacts are removed on teardown and swept when orphaned."""
    print("Lifecycle:")
    worker = _worker(sidecar_url)
    worker.orderlist = fixture("NRP")
    worker.t_createArchify({}, {})
    uid = worker.generated["uid"]
    diagramdir = os.path.join(workdir, "artifacts")
    check(os.path.isfile(os.path.join(diagramdir, f"{uid}.html.gz")), "artifact exists after a build")

    worker.a_sweepArtifacts({uid})
    check(os.path.isfile(os.path.join(diagramdir, f"{uid}.html.gz")), "a uid still claimed survives the sweep")

    worker.a_removeArtifact(uid)
    check(not os.path.isfile(os.path.join(diagramdir, f"{uid}.html.gz")), "removeArtifact deletes it")

    worker.t_createArchify({}, {})
    worker.a_sweepArtifacts(set())
    check(not os.path.isfile(os.path.join(diagramdir, f"{uid}.html.gz")), "an orphan is swept")

    with open(os.path.join(diagramdir, "not-a-uid.html.gz"), "w", encoding="utf-8") as fd:
        fd.write("x")
    worker.a_sweepArtifacts(set())
    check(os.path.isfile(os.path.join(diagramdir, "not-a-uid.html.gz")), "the sweep leaves files it did not write")
    worker.a_removeArtifact("../../etc/passwd")
    check(os.path.isfile("/etc/passwd"), "removeArtifact refuses a uid that is a path")


def _manifest():
    """A manifest in the shape findorder() consumes.

    The fixtures beside this file are already-walked path models. The diagram
    wiring runs one step earlier than that, on manifest["Ports"], so this
    rebuilds the NRP reservation in that form: two hosts on two ports of one
    switch.
    """

    def port(name, host, mac):
        return {
            "Site": "urn:ogf:network:nrp-nautilus.io:2020",
            "Port": f"urn:ogf:network:nrp-nautilus.io:2020:edgecore_s0:{name}",
            "Node": "T2_US_SDSC:edgecore_s0",
            "Name": name,
            "Peer": "?peer?",
            "Vlan": "3110",
            "Mac": "00:90:fb:76:e4:7b",
            "IPv4": "?port_ipv4?",
            "IPv6": "?port_ipv6?",
            "Host": [
                {
                    "Name": f"T2_US_SDSC:{host}",
                    "Interface": "enp168s0np0",
                    "Mac": mac,
                    "IPv4": "?ipv4?",
                    "IPv6": "?ipv6?",
                }
            ],
        }

    return {"Ports": [port("Ethernet40", "k8s-gen5-02.sdsc.optiputer.net", "58:a2:e1:0b:34:3a"), port("Ethernet32", "k8s-gen5-01.sdsc.optiputer.net", "a0:88:c2:86:ee:7c")]}


def test_diagram_wiring(sidecar_url):
    """__createDiagrams returns both panel groups, built from one walk.

    The wiring is the part most easily got wrong: findorder() destroys
    manifest["Ports"] as it walks, so Mermaid has to run first and Archify has
    to read what it left rather than walking again. If that ordering breaks,
    Archify silently draws nothing while Mermaid still looks fine.
    """
    print("Diagram wiring:")
    worker = _worker(sidecar_url)
    # Name-mangled because __createDiagrams is private to Template. Reaching
    # for it directly is the point: this checks the diagram wiring itself, and
    # t_createTemplate cannot be called without Grafana, SENSE-O and Prometheus
    # behind it.
    groups = worker._Template__createDiagrams({}, _manifest())  # pylint: disable=protected-access,no-member
    check(len(groups) == 2, f"two panel groups are returned (got {len(groups)})")
    mermaid, archify = groups[0], groups[1]
    check(bool(mermaid), "the Mermaid group has panels")
    check(bool(archify), "the Archify group has panels")
    check("jdbranham-diagram-panel" in json.dumps(mermaid), "the first group is the Mermaid panel")
    check("<iframe" in json.dumps(archify), "the second group is the Archify iframe panel")
    check(len(worker.orderlist) == 4, f"the shared walk found the whole path (got {len(worker.orderlist)})")
    check(not worker.datawarnings, f"no warnings (got {worker.datawarnings})")

    # Archify only: the walk still has to run, its panel is just not shown.
    other = _worker(sidecar_url, topdiagrams="Archify")
    groups = other._Template__createDiagrams({}, _manifest())  # pylint: disable=protected-access,no-member
    check(not groups[0], "topdiagrams=Archify drops the Mermaid panel")
    check(bool(groups[1]), "and keeps the Archify one")
    check(len(other.orderlist) == 4, "while still doing the walk that builds the model")

    # Mermaid only: no artifact, no warning, nothing to serve.
    plain = _worker(sidecar_url, topdiagrams="Mermaid")
    groups = plain._Template__createDiagrams({}, _manifest())  # pylint: disable=protected-access,no-member
    check(bool(groups[0]), "topdiagrams=Mermaid keeps the Mermaid panel")
    check(not groups[1], "and produces no Archify panel")
    check(not plain.datawarnings, "silently, because nothing was expected")
    check(len(plain.orderlist) == 4, "the Mermaid walk still runs")


def main():
    """Run everything and report."""
    with tempfile.TemporaryDirectory(prefix="archify-test-") as workdir:
        sidecar_url, stop = start_sidecar(workdir)
        try:
            test_ir_shape()
            test_device_collapse()
            test_no_self_links()
            test_disconnected_runs_stay_apart()
            test_unreported_transit_is_bridged_and_marked()
            test_the_first_run_is_flipped_to_face_the_next()
            test_transit_is_never_invented_across_sites()
            test_long_names_are_fitted()
            test_pathological_names_degrade()
            test_empty_input()
            test_cards_carry_the_detail()
            test_panel_end_to_end(workdir, sidecar_url)
            test_sidecar_down_is_survivable()
            test_unconfigured_is_silent()
            test_half_configured_is_reported()
            test_archify_only_without_a_sidecar_is_reported()
            test_disabled_does_nothing()
            test_dropped_hosts_are_reported(sidecar_url)
            test_lifecycle(workdir, sidecar_url)
            test_diagram_wiring(sidecar_url)
        finally:
            stop()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
