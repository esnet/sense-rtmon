#!/usr/bin/env python3
"""Archify topology panel: artifact generation and lifecycle.

The second of the two top-of-dashboard diagrams. Mermaid draws the complete
graph - every port, VLAN, address and BGP peer - and this draws the path at
device level, with the detail moved into cards beside it. Both are rendered,
because they answer different questions and neither replaces the other.

Split from ArchifyIR on purpose: everything that talks to the network is
here, and the IR construction next door stays a pure function of the path
model, which is what lets test/test_archify.py check the interesting half
without a deployment.

The Archify runtime itself does not live in this repository. It is a Node
runtime and a large vendored JavaScript tree, and folding it in would put both
in every RTMon image whether or not the operator draws this panel, so it runs
in a sidecar and the cost falls only on deployments that opt in.

What this class depends on is therefore an interface, not a particular
program: something that accepts the IR at POST /v1/render and serves the
result at GET /diagrams/<uid>.html, plus the sweep and delete endpoints used
at teardown. The README's topology section writes the contract out.
github.com/groundsada/rtmon-archify is the reference implementation of it.

This class is only the client: build the IR, POST it, point the panel's
iframe at the served URL. Everything else - the fallback ladder, the sweep,
the teardown - stays here, because the failure budget of a dashboard belongs
with the thing that owns the dashboard.

The output is one self-contained ~200 KB (gzipped) HTML file per dashboard,
owned and served by the sidecar. It is not inlined into the dashboard JSON:
the archify runtime shell alone is 760 KB before any diagram is drawn, so
every dashboard would carry most of a megabyte of identical payload into
Grafana's database.

Nothing here is allowed to fail a dashboard. Sidecar down, renderer rejecting
the layout, a render that hangs - each one ends the same way, with a warning
in the dashboard's own "Graph Generation Warnings" row and no Archify panel.
The Mermaid panel is right there and still complete.
"""

# E1101: a mixin. config, logger, generated, orderlist, m_groups and the
# t_ helpers are provided by the classes this is composed with in RTMonWorker,
# the same arrangement Template and DataWarnings are in.
# line-too-long: the warning strings are prose the operator reads on the
# dashboard, and wrapping them to 120 columns does not make them clearer.
# pylint: disable=E1101,line-too-long
import re

import requests

from RTMonLibs.ArchifyIR import buildIR

# Artifact names are dashboard uids, which t_createDashboard derives with
# uuid5. Anything else is not ours: this pattern is what the generator writes
# and what the sidecar agrees to serve, so path traversal is closed off by
# the shape of the name rather than by normalising a caller-supplied path.
UID_RE = re.compile(r"^[0-9a-fA-F-]{8,40}$")

# Degradation ladder. Each rung strips one tier of richness and re-validates,
# so the loop converges on something renderable instead of trying to reverse
# engineer a fix out of diagnostic prose. Ordered by what costs least to lose.
LADDER = ("full", "shorttext", "nolabels", "bare")

# Text budgets per rung, passed through to the IR builder.
SHORT_LABEL = 16
SHORT_SUBLABEL = 24


class Archify:
    """Archify topology artifacts for the dashboards this worker owns."""

    def _a_cfg(self, key, default=None):
        """One archify setting, with the operator's default."""
        return (self.config.get("archify", {}) or {}).get(key, default)

    def _a_selected(self):
        """Whether topdiagrams asks for the Archify panel.

        topdiagrams is the selector both diagrams share: Mermaid, Archify or
        Both. It shipped as a dead key naming only Mermaid; reviving it here is
        cheaper than adding a second knob that means the same thing.
        """
        return str(self.config.get("topdiagrams", "Both")).lower() in ("archify", "both")

    def a_configured(self):
        """Whether an operator has pointed this deployment at a sidecar.

        The panel needs a renderer to call and a URL a browser can fetch the
        result from, and neither has a default worth guessing. An install that
        has set neither is one that is not using the feature.

        REPLACEME counts as unset: it is what the shipped config carries, so
        treating it as a value would make every default install look like a
        deployment that had been configured and then broken.
        """
        return any(value and "REPLACEME" not in value for value in (self._a_url(), str(self._a_cfg("diagram_url_base", "") or "")))

    def _a_optedOut(self):
        """True when this install is not drawing the panel, having said so if
        that is worth saying.

        Silent when topdiagrams leaves Archify out, and silent when nothing is
        configured and topdiagrams is Both: Mermaid is still drawn and the
        install is simply not using this. Loud when topdiagrams is Archify and
        no sidecar is configured, because that asked for this panel and would
        otherwise leave the dashboard with no topology diagram and no reason.
        """
        if not self._a_selected():
            return True
        if not self.a_configured():
            if str(self.config.get("topdiagrams", "Both")).lower() == "archify":
                self.t_recordWarning(
                    "No topology diagram is shown because topdiagrams is set to Archify but the archify sidecar is not configured. Set archify.sidecar_url and archify.diagram_url_base, or set topdiagrams to Mermaid."
                )
            return True
        return False

    def a_enabled(self):
        """Whether this deployment draws the Archify panel at all.

        Opt-in, and silent when it is opted out of. The panel needs a sidecar
        that an upgrade does not bring with it, so a default install must not
        start reporting a missing one: an RTMon that has never been pointed at
        a sidecar is not misconfigured, it is just not using this.

        Being half-configured is different, and still warns - see
        t_createArchify. So does asking for topdiagrams: Archify without a
        sidecar, because that is an operator who has said what they want and
        would otherwise get a dashboard with no topology diagram on it at all.
        """
        return self._a_selected() and self.a_configured()

    def _a_url(self):
        """The sidecar base URL, if configured."""
        return str(self._a_cfg("sidecar_url", "") or "").rstrip("/")

    def _a_headers(self):
        """Auth header for the write endpoints, if a token is configured."""
        token = self._a_cfg("token", "")
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _a_post(self, path, payload, timeout):
        """POST JSON to the sidecar. Never raises; (ok, status, body)."""
        try:
            response = requests.post(
                f"{self._a_url()}{path}",
                json=payload,
                headers=self._a_headers(),
                timeout=timeout,
            )
        except requests.RequestException as ex:
            return False, 0, {"error": f"could not reach the Archify sidecar: {ex}"}
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        return response.status_code in (200, 201), response.status_code, body

    def _a_delete(self, uid):
        """DELETE one artifact on the sidecar. Never raises."""
        try:
            requests.delete(
                f"{self._a_url()}/api/v1/artifacts/{uid}",
                headers=self._a_headers(),
                timeout=30,
            )
        except requests.RequestException as ex:
            self.logger.warning("Could not reach the Archify sidecar: %s", ex)

    def _a_attempt(self, rung, uid, timeout, args):
        """One rung: build, POST. Returns (ok, report, detail).

        detail is empty on success and carries the renderer's first complaint
        otherwise, so the caller can report why the last rung failed rather
        than only that it did.
        """
        ir, report = self._a_buildFor(rung, args[0], args[1], output=f"{uid}.html", **args[2])
        if ir is None:
            return None, report, "the manifest produced no devices to draw"
        ok, status, body = self._a_post("/v1/render", {"uid": uid, "ir": ir, "quality": self._a_cfg("quality", "standard")}, timeout)
        if ok:
            return True, report, ""
        if status == 422:
            diagnostics = [str(d.get("message", "")).split("\n", 1)[0] for d in body.get("diagnostics", []) or []]
            return False, report, "; ".join(d for d in diagnostics if d)[:400]
        return False, report, str(body.get("error", "") or "the sidecar refused the diagram")[:400]

    @staticmethod
    def _a_buildFor(rung, orderlist, instance, **kwargs):
        """The IR for one rung of the ladder."""
        if rung in ("shorttext", "nolabels", "bare"):
            kwargs = dict(kwargs, labelmax=SHORT_LABEL, sublabelmax=SHORT_SUBLABEL)
        ir, report = buildIR(orderlist, instance, **kwargs)
        if ir is None:
            return None, report
        return Archify._a_degrade(ir, rung), report

    @staticmethod
    def _a_degrade(ir, rung):
        """Strip one tier of richness off the IR. Returns a new dict."""
        if rung == "full":
            return ir
        out = dict(ir)
        if rung in ("nolabels", "bare"):
            out["connections"] = [{k: v for k, v in c.items() if k not in ("label", "labelAt")} for c in ir.get("connections", [])]
        if rung == "bare":
            out["boundaries"] = []
            meta = dict(out["meta"])
            meta["views"] = []
            out["meta"] = meta
        return out

    def _a_subtitle(self, instance):
        """A one line summary of the path, for under the diagram title."""
        sites = set()
        for group in ("Hosts", "Switches"):
            for key in self.m_groups.get(group, {}):
                sites.add(str(key).split(":", maxsplit=1)[0])
        hosts = len(self.m_groups.get("Hosts", {}))
        alias = (instance or {}).get("alias", "")
        summary = f"{len(sites)} site(s) · {hosts} endpoint(s)"
        return f"{summary} · {alias}" if alias else summary

    def _a_compile(self, orderlist, instance, uid, **kwargs):
        """POST to the sidecar, degrading until something passes.

        Returns (ok, report, detail). The ladder is walked rather than the
        diagnostics parsed: every rung is strictly simpler than the one before
        it, so this terminates, and it does not depend on the exact wording the
        renderer happens to use for a rejection.
        """
        timeout = int(self._a_cfg("render_timeout", 60))
        rounds = max(int(self._a_cfg("max_fix_rounds", 3)), 0)
        report, detail = {}, "no attempt was made"
        for rung in LADDER[: rounds + 1]:
            ok, report, detail = self._a_attempt(rung, uid, timeout, (orderlist, instance, kwargs))
            if ok is None:
                # Nothing to draw. No later rung can conjure a device, so the
                # ladder has nowhere to go.
                break
            if not ok:
                self.logger.info("Archify rung %s failed for %s: %s", rung, uid, detail)
                continue
            if rung != LADDER[0]:
                self.logger.info("Archify fell back to rung %s for %s", rung, uid)
            return True, report, ""
        return False, report, detail

    def a_removeArtifact(self, uid):
        """Drop the sidecar artifact belonging to one dashboard uid."""
        if not uid or not self.a_enabled():
            return
        if not UID_RE.match(str(uid)):
            self.logger.error("Refusing to remove Archify artifacts for a uid that is not one: %r", uid)
            return
        self._a_delete(str(uid))

    def a_sweepArtifacts(self, knownuids):
        """Tell the sidecar which uids are still claimed; it removes the rest.

        _removeDashboard covers the ordinary teardown. This covers what it
        cannot: a crash between writing the artifact and writing the state
        file, a dashboard deleted by hand in Grafana, or a state file lost. An
        artifact nothing points at is otherwise kept until the volume fills.

        The caller guarantees the keep set is complete before calling this
        (see _sweepArtifactsIfSafe in worker.py). Only uid-shaped uids reach
        the sidecar.
        """
        if not self.a_enabled():
            return 0
        keep = [str(uid) for uid in knownuids if uid and UID_RE.match(str(uid))]
        ok, _status, body = self._a_post("/api/v1/sweep", {"keep": keep}, 60)
        if not ok:
            self.logger.warning("Could not sweep Archify artifacts: %s", body.get("error", body))
            return 0
        removed = int(body.get("removed", 0) or 0)
        if removed:
            self.logger.info("Swept %s orphaned Archify artifact(s)", removed)
        return removed

    def a_artifactURL(self, uid):
        """The URL the panel's iframe points at, or None if not configured.

        There is no sensible guess for this. What the sidecar serves and what
        a browser can reach are related only by whatever Service, Ingress and
        TLS the deployment puts in front of it, so an unset diagram_url_base
        means no panel rather than a link to somewhere that does not exist.
        """
        base = str(self._a_cfg("diagram_url_base", "") or "").rstrip("/")
        if not base or "REPLACEME" in base:
            return None
        return f"{base}/{uid}.html"

    def t_createArchify(self, *args, **kwargs):
        """The Archify topology panel, or nothing plus a warning.

        Runs after the Mermaid panel has been built, and reads the path model
        that walk left behind rather than the manifest: findorder() consumes
        manifest["Ports"] as it goes, so there is only one walk available and
        both diagrams are drawn from it.
        """
        if self._a_optedOut():
            return []
        uid = self.generated.get("uid", "")
        if not uid or not UID_RE.match(str(uid)):
            self.logger.error("No usable dashboard uid for the Archify panel: %r", uid)
            return []
        url = self.a_artifactURL(uid)
        if not url:
            self.t_recordWarning("The interactive topology diagram is not shown because archify.diagram_url_base is not configured.")
            return []
        if not self._a_url():
            self.t_recordWarning("The interactive topology diagram is not shown because archify.sidecar_url is not configured.")
            return []
        instance = args[0] if args else {}
        title = self.generated.get("title", "End-to-End Flow Topology")
        ok, report, detail = self._a_compile(
            self.orderlist,
            instance,
            str(uid),
            title=title,
            subtitle=self._a_subtitle(instance),
            quality=self._a_cfg("quality", "standard"),
        )
        for dropped in report.get("dropped", []):
            self.t_recordWarning(f"Host {dropped} is not drawn on the interactive topology diagram, which shows at most two hosts per switch. It is shown in full on the Mermaid diagram above.")
        if not ok:
            self.t_recordWarning(f"The interactive topology diagram could not be generated, so only the Mermaid diagram is shown. Reason: {detail}")
            return []
        row = self.t_addRow(*args, title="End-to-End Flow Topology (Archify)", collapsed=kwargs.get("collapsed", False))
        panel = self._t_loadTemplate("archify.json")
        panel["options"]["content"] = panel["options"]["content"].replace("REPLACEME_ARCHIFY_URL", url)
        return self.addRowPanel(row, [panel])
