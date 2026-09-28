#!/usr/bin/env python3
"""Read-only HTTP API exposing the SiteRM debug action results RTMon caches.

Two consumers, one surface:

  Grafana         reads it through the Infinity datasource, which can carry a
                  static bearer token and nothing else.
  People, and in
  time the SENSE
  dashboard       arrive with a Keycloak token from the realm they already log
                  into, so a request says who asked rather than only that
                  somebody knew the shared token.

Only GET is served. The routing, the auth and the role check are shaped for the
submit endpoints the dashboard will want later, but nothing here writes to a
site, so a leaked read token cannot start a transfer on somebody's host.

Results come from the state files the worker writes, never from a live call to a
frontend: a Grafana panel refreshing every 30s must not turn into load on every
SiteRM on the path. SiteRMApi.sr_refresh_results keeps those files current.
"""
import hmac
import json
import os
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from RTMonLibs.GeneralLibs import loadFileJson

JWKS_TTL = 300
STATE_PREFIX = "rtmon-debug-"


class Unauthorised(Exception):
    """Raised when a request cannot be attributed to a caller we accept."""


# One Authenticator per process, so the JWKS refresh guard is module wide.
_JWKS_LOCK = threading.Lock()


# One public method is the whole interface: a caller either is or is not
# admitted, and everything else here is how that answer is reached.
class Authenticator:  # pylint: disable=too-few-public-methods
    """Bearer token for Grafana, Keycloak JWT for everyone else.

    With neither configured every request is refused. An endpoint that is only
    reachable inside the cluster is still reachable by every pod in the
    namespace, and defaulting to open is how that stops being obvious.
    """

    def __init__(self, config, logger):
        self.logger = logger
        self.token = str(config.get("http_api_token", "") or "")
        self.issuer = str(config.get("http_api_oidc_issuer", "") or "").rstrip("/")
        self.audience = str(config.get("http_api_oidc_audience", "") or "")
        roles = config.get("http_api_oidc_roles", []) or []
        self.roles = [roles] if isinstance(roles, str) else list(roles)
        self.jwt = self._loadjwt()
        self._jwks = {"at": 0.0, "client": None}
        if not self.token and not self.issuer:
            self.logger.error("Neither http_api_token nor http_api_oidc_issuer is set. "
                              "The results API will refuse every request.")

    def _loadjwt(self):
        """PyJWT if the image has it, otherwise None and bearer only."""
        if not self.issuer:
            return None
        try:
            import jwt  # pylint: disable=import-outside-toplevel

            return jwt
        except ImportError:
            # An older image predates the dependency. Saying so once is better
            # than every Keycloak caller getting an opaque 401.
            self.logger.error("http_api_oidc_issuer is set but PyJWT is not installed. "
                              "Only the static bearer token will be accepted.")
            return None

    def _jwksclient(self):
        """Cached PyJWKClient, refetched when the realm rotates its keys."""
        with _JWKS_LOCK:
            now = time.time()
            if self._jwks["client"] and (now - self._jwks["at"]) < JWKS_TTL:
                return self._jwks["client"]
            client = self.jwt.PyJWKClient(f"{self.issuer}/protocol/openid-connect/certs")
            self._jwks.update(at=now, client=client)
            return client

    def _hasrole(self, claims):
        """No configured roles means any valid token from the realm admits."""
        if not self.roles:
            return True
        held = set(claims.get("realm_access", {}).get("roles", []))
        for client in claims.get("resource_access", {}).values():
            held.update(client.get("roles", []))
        return bool(held.intersection(self.roles))

    def _checkjwt(self, token):
        """Validated identity from a realm token, or raise Unauthorised."""
        try:
            key = self._jwksclient().get_signing_key_from_jwt(token)
            claims = self.jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience or None,
                options={"verify_aud": bool(self.audience)},
            )
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # Deliberately broad: PyJWT raises a family of distinct errors for
            # expiry, bad signature, wrong issuer and a malformed JWKS reply,
            # and all of them mean the same thing to the caller.
            raise Unauthorised(f"token rejected: {type(ex).__name__}") from ex
        if not self._hasrole(claims):
            raise Unauthorised("token carries none of the required roles")
        return claims.get("email") or claims.get("preferred_username") or claims.get("sub") or "keycloak"

    def check(self, header):
        """Identity of the caller, or raise Unauthorised."""
        if not header or not header.lower().startswith("bearer "):
            raise Unauthorised("no bearer credential")
        presented = header.split(" ", 1)[1].strip()
        if not presented:
            raise Unauthorised("empty bearer credential")
        if self.token and hmac.compare_digest(presented, self.token):
            return "grafana"
        if self.jwt:
            return self._checkjwt(presented)
        raise Unauthorised("credential did not match the configured token")


class ResultsStore:
    """The cached action results, read out of the worker's state files."""

    # Copied verbatim from each cached entry onto the flat row.
    carried = ("id", "sitename", "hostname", "state", "exitcode", "inserted",
               "updated", "fetched", "truncated", "totallines", "jsonout")

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def _statefiles(self):
        """Every state file, as (filename, parsed). Unreadable ones are skipped."""
        workdir = self.config.get("workdir", "/srv")
        for root, _, files in os.walk(workdir):
            for filename in files:
                # .tmp is the half written file _updateState is about to move
                # over the real one, and carries the same prefix.
                if not filename.startswith(STATE_PREFIX) or filename.endswith(".tmp"):
                    continue
                fout = loadFileJson(os.path.join(root, filename), self.logger)
                if fout:
                    yield filename, fout

    @staticmethod
    def _describe(fout):
        """The identifying fields every row and summary carries."""
        return {
            "instance": fout.get("referenceUUID", ""),
            "orchestrator": fout.get("orchestrator", ""),
            "alias": fout.get("instance", {}).get("alias", ""),
        }

    def instances(self):
        """One summary per path RTMon is monitoring."""
        out = []
        for _, fout in self._statefiles():
            row = self._describe(fout)
            row["state"] = fout.get("state", "")
            row["actions"] = sorted(fout.get("action_results", {}))
            out.append(row)
        return sorted(out, key=lambda item: item["instance"])

    def results(self, filters):
        """Flat rows, one per submitted action, newest first.

        Flat rather than nested because that is what a Grafana table wants; the
        structured form the site returned is kept alongside as jsonout for the
        panels that can use it.
        """
        out = []
        for _, fout in self._statefiles():
            base = self._describe(fout)
            if filters.get("instance") and filters["instance"] != base["instance"]:
                continue
            for action, entries in fout.get("action_results", {}).items():
                if filters.get("action") and filters["action"] != action:
                    continue
                for entry in entries:
                    row = dict(base)
                    row["action"] = action
                    row.update({key: entry.get(key) for key in self.carried})
                    row["type"] = entry.get("action", "")
                    row["output"] = "\n".join(entry.get("lines", []))
                    if filters.get("sitename") and filters["sitename"] != row["sitename"]:
                        continue
                    if filters.get("state") and filters["state"] != row["state"]:
                        continue
                    out.append(row)
        return sorted(out, key=lambda item: (item.get("updated") or 0), reverse=True)

    def sitermwarnings(self, filters):
        """Flat rows of what each site says about its own services (#261).

        A site that could not be asked gets a row of its own rather than no rows.
        "nothing is wrong" and "nobody checked" are the two answers an operator
        must not have to tell apart by absence.
        """
        out = []
        for _, fout in self._statefiles():
            base = self._describe(fout)
            if filters.get("instance") and filters["instance"] != base["instance"]:
                continue
            for sitename, state in fout.get("siterm_states", {}).items():
                if filters.get("sitename") and filters["sitename"] != sitename:
                    continue
                rows = [dict(base, sitename=sitename, checked=state.get("checked"),
                             services=state.get("total"), **warn)
                        for warn in state.get("warnings", [])]
                if not rows and state.get("reason"):
                    rows = [dict(base, sitename=sitename, checked=state.get("checked"),
                                 services=state.get("total"), hostname="", servicename="",
                                 servicestate="NOT CHECKED" if state.get("managed") else "NOT MANAGED",
                                 version="", runtime=None, exccode=None,
                                 exc=state.get("reason"), updated=state.get("checked"))]
                for row in rows:
                    if filters.get("state") and filters["state"] != row["servicestate"]:
                        continue
                    out.append(row)
        return sorted(out, key=lambda item: (item.get("updated") or 0), reverse=True)


def makeHandler(store, auth, logger):
    """Build the request handler bound to one store and one authenticator."""

    class Handler(BaseHTTPRequestHandler):
        """Read-only results endpoint."""

        server_version = "RTMon"
        sys_version = ""

        def log_message(self, format, *args):  # pylint: disable=redefined-builtin
            """Access logging through RTMon's logger instead of stderr."""
            logger.info("results-api %s %s", self.address_string(), format % args)

        def _respond(self, code, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        @staticmethod
        def _filters(query):
            """Recognised filters, and the ones that were not recognised.

            Returned rather than ignored: a filter that is silently dropped
            answers with everything, which reads as a complete answer to a
            question nobody asked.
            """
            known = ("instance", "action", "sitename", "state")
            out = {}
            unknown = []
            for part in query.split("&"):
                if "=" not in part:
                    continue
                key, _, value = part.partition("=")
                key = urllib.parse.unquote_plus(key)
                if key in known:
                    out[key] = urllib.parse.unquote_plus(value)
                else:
                    unknown.append(key)
            return out, unknown

        def do_GET(self):  # pylint: disable=invalid-name
            """Route a read. Anything not listed here is a 404, including writes."""
            path, _, query = self.path.partition("?")
            path = path.rstrip("/") or "/"
            if path in ("/healthz", "/"):
                # Deliberately unauthenticated: it is the kubelet probe, and it
                # reports nothing but that the process is answering.
                self._respond(200, {"status": "ok"})
                return
            try:
                identity = auth.check(self.headers.get("Authorization", ""))
            except Unauthorised as ex:
                logger.warning("results-api refused %s for %s: %s", self.address_string(), path, ex)
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Bearer realm="rtmon"')
                self.end_headers()
                return
            logger.debug("results-api serving %s to %s", path, identity)
            if path == "/api/v1/instances":
                self._respond(200, store.instances())
                return
            served = {"/api/v1/results": store.results,
                      "/api/v1/sitermwarnings": store.sitermwarnings}
            if path in served:
                filters, unknown = self._filters(query)
                if unknown:
                    self._respond(400, {"error": "unknown filters", "filters": sorted(set(unknown))})
                    return
                self._respond(200, served[path](filters))
                return
            self._respond(404, {"error": "not found", "path": path})

    return Handler


def serve(config, logger):
    """Run the results API until the process is stopped."""
    port = int(config.get("http_api_port", 8080))
    bind = str(config.get("http_api_bind", "0.0.0.0"))
    store = ResultsStore(config, logger)
    auth = Authenticator(config, logger)
    httpd = ThreadingHTTPServer((bind, port), makeHandler(store, auth, logger))
    logger.info("Results API listening on %s:%s", bind, port)
    httpd.serve_forever()
