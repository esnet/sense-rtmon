#!/usr/bin/env node
// RTMon Archify sidecar: render and serve topology artifacts.
//
// This is the service half of the RTMon Archify panel. RTMon builds the
// Archify IR (the SENSE path model rendered to Archify's typed JSON) and POSTs
// it here; this validates it with Archify's own validator, renders it, appends
// the MIT/OFL attribution, and stages the gzipped result. GETs are what the
// dashboard iframe fetches. That is the whole job.
//
// Why a separate container: the payload is Archify's MIT-licensed runtime plus
// the upstream third-party brand artwork tree. Keeping that out of the ESnet
// repo and image means the only third-party code in RTMon is none; this sidecar
// is where the third-party tree lives, and its licence posture is this repo's
// to declare.
//
// Auth split: the GET path is what a browser iframe hits, so it carries no
// secret. Everything that writes (render, delete, list) needs the bearer token;
// until one is configured those endpoints answer 503 rather than running open,
// because a renderer that accepts arbitrary POSTs is an arbitrary-code-exec
// surface on the same pod.
//
// API:
//   GET    /healthz                      -> {ok, version, schemaVersion}
//   POST   /v1/render                    {uid, ir, [quality]}
//   GET    /diagrams/<uid>.html          gzipped artifact, public
//   GET    /api/v1/artifacts             [uid, ...] (auth)
//   DELETE /api/v1/artifacts/<uid>       (auth)
//   POST   /api/v1/sweep                 {keep: [uid, ...]} (auth)
//
// Route discipline is the same as the RTMon-Diagrams server it replaces: only a
// uid-shaped segment is ever taken from a request, it is never used to build a
// path before it has matched, and failures are uniform 404s with no body that
// names what went wrong.
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const UID_RE = /^[0-9a-fA-F-]{8,40}$/;
const BODY_LIMIT = 4 * 1024 * 1024; // 4 MiB of IR is a lot of diagram
const VERSION = fs.existsSync(path.join(__dirname, "archify-cli", "VERSION"))
  ? fs
      .readFileSync(path.join(__dirname, "archify-cli", "VERSION"), "utf8")
      .trim()
  : "unknown";

// Appended to every published artifact. A rendered diagram embeds Archify's
// own viewer script, so serving one redistributes a substantial portion of
// MIT licensed software, and the MIT licence asks that its notice travel with
// it. Upstream's template carries the SIL OFL text for the embedded JetBrains
// Mono subset but no notice of its own, so this supplies it.
//
// Appended after </html> rather than prepended: a comment ahead of the
// DOCTYPE puts some browsers into quirks mode, which would change how the
// diagram is laid out. Trailing content is ignored by every parser.
const ATTRIBUTION = Buffer.from(`\n<!--
Rendered by Archify (https://github.com/tt-a1i/archify), MIT licence.
Copyright (c) 2026 tt-a1i (Archify). Copyright (c) 2025 Cocoon AI.
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the Software),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
The embedded JetBrains Mono subset is under the SIL Open Font License 1.1;
its text is carried in the font CSS above.
-->\n`);

// The artifact ships sixteen controls on arrival - four in the toolbar, four
// guided-view buttons, eight on the diagram nav. On a Grafana dashboard the
// panel is a diagram first and a tool second, so they start folded behind one
// button and everything is one click away.
//
// Appended rather than rendered, for the same reason the attribution is: the
// renderer is vendored upstream code and is not edited here. The toggle goes
// *inside* .toolbar so it inherits the artifact's own button styling and
// cannot overlap the controls it reveals, and the collapse is driven by one
// attribute on <html> rather than by setting display on the elements, so the
// diagram's own show/hide logic still owns them once they are visible.
const CHROME_TOGGLE = Buffer.from(`
<style>
html[data-rtmon-chrome="hidden"] .toolbar > *:not(.rtmon-chrome-toggle),
html[data-rtmon-chrome="hidden"] .guided-views,
html[data-rtmon-chrome="hidden"] .diagram-nav { display: none !important; }
.rtmon-chrome-toggle { cursor: pointer; }
@media print { .rtmon-chrome-toggle { display: none !important; } }
</style>
<script>
(function () {
  var root = document.documentElement;
  if (root.dataset.rtmonChrome === 'off') return;
  var START = root.dataset.rtmonChrome || 'hidden';
  var tries = 0;
  function mount() {
    var bar = document.querySelector('.toolbar');
    // The toolbar is built by the artifact's own script, so it may not exist
    // on the first frame. Give up quietly rather than leave a dead observer:
    // no toggle just means the controls stay visible, which is the old
    // behaviour and not a broken panel.
    if (!bar) { if (++tries < 60) requestAnimationFrame(mount); return; }
    if (bar.querySelector('.rtmon-chrome-toggle')) return;
    root.dataset.rtmonChrome = START;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'rtmon-chrome-toggle';
    function sync() {
      var hidden = root.dataset.rtmonChrome === 'hidden';
      btn.textContent = hidden ? 'Controls' : 'Hide controls';
      btn.setAttribute('aria-expanded', hidden ? 'false' : 'true');
      btn.setAttribute('aria-label', hidden ? 'Show diagram controls' : 'Hide diagram controls');
    }
    btn.addEventListener('click', function () {
      root.dataset.rtmonChrome = root.dataset.rtmonChrome === 'hidden' ? 'shown' : 'hidden';
      sync();
    });
    sync();
    bar.insertBefore(btn, bar.firstChild);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
</script>
`);

function json(res, code, body) {
  const payload = Buffer.from(JSON.stringify(body));
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": payload.length,
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
  });
  res.end(payload);
}

function deny(res) {
  // Always 404, never 403, never a message naming what was wrong. A
  // distinguishable "forbidden" tells a caller that the name it tried is
  // meaningful, which is the first half of enumerating the directory.
  const body = Buffer.from("not found\n");
  res.writeHead(404, {
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": body.length,
    "X-Content-Type-Options": "nosniff",
  });
  res.end(body);
}

function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > limit) {
        reject(
          Object.assign(new Error("request body too large"), { code: 413 }),
        );
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function uidFromRequest(raw) {
  const pathname = (raw || "").split("?", 1)[0].split("#", 1)[0];
  const match = /^\/diagrams\/([0-9a-fA-F-]{8,40})\.html$/.exec(pathname);
  if (!match || !UID_RE.test(match[1])) return null;
  return match[1];
}

class Archive {
  /**
   * The artifact store. One directory; the uid is the only thing that ever
   * becomes part of a filename, and only after UID_RE has accepted it.
   */
  constructor(dir, cli, quality, chrome) {
    this.dir = dir;
    this.cli = cli;
    this.quality = quality; // request value wins; this is the default
    // hidden (default) | shown | off. "off" appends nothing at all, so an
    // artifact is exactly what the renderer produced.
    this.chrome = ["hidden", "shown", "off"].includes(chrome)
      ? chrome
      : "hidden";
    fs.mkdirSync(dir, { recursive: true });
  }

  _trailer() {
    if (this.chrome === "off") return [ATTRIBUTION];
    // The start state rides on <html> so the toggle script reads it rather
    // than this server having to template the script itself.
    const start = Buffer.from(
      `\n<script>document.documentElement.dataset.rtmonChrome=${JSON.stringify(this.chrome)}</script>\n`,
    );
    // Attribution stays last. The licence notice ending the file is a posture
    // this repo takes deliberately and a test asserts, so the toggle goes
    // ahead of it rather than after.
    return [start, CHROME_TOGGLE, ATTRIBUTION];
  }

  _name(uid) {
    return path.join(this.dir, `${uid}.html.gz`);
  }

  _tmpName(uid) {
    return path.join(this.dir, `.${uid}.tmp`);
  }

  _run(args, env) {
    return spawnSync(process.execPath, [this.cli, ...args], {
      encoding: "utf8",
      timeout: 120000,
      env: { ...process.env, ...env },
    });
  }

  render(uid, ir, quality) {
    /**
     * Validate, then render. Returns {ok, bytes, diagnostics, error}.
     * The caller in RTMon owns the fallback ladder: a 422 carries the
     * validator's diagnostics so it knows what to strip next, never a guess
     * about what this side caches.
     */
    const profile = ["standard", "showcase"].includes(quality)
      ? quality
      : this.quality;
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "archify-rtmon-"));
    const irPath = path.join(tmp, `${uid}.json`);
    const htmlPath = path.join(tmp, `${uid}.html`);
    try {
      fs.writeFileSync(irPath, JSON.stringify(ir));
      const validate = this._run(
        ["validate", "architecture", irPath, "--json", "--quality", profile],
        { ARCHIFY_DIAGNOSTIC_FORMAT: "json" },
      );
      if (validate.status !== 0) {
        const diagnostics = [];
        try {
          const receipt = JSON.parse(validate.stdout);
          if (Array.isArray(receipt.diagnostics))
            diagnostics.push(...receipt.diagnostics);
        } catch {
          /* non-JSON failure, keep the raw stderr */
        }
        let error = validate.stderr || validate.stdout || "unknown";
        // The validate helper prints the diagnostics as a receipt on stdout
        // for --json failures; stderr holds only its own prose.
        return { ok: false, diagnostics, error: error.trim().slice(0, 400) };
      }
      const render = this._run(
        ["render", "architecture", irPath, htmlPath, "--quality", profile],
        {},
      );
      if (render.status !== 0) {
        const error = (render.stderr || render.stdout || "unknown")
          .trim()
          .slice(0, 400);
        return { ok: false, diagnostics: [], error };
      }
      const gz = zlib.gzipSync(
        Buffer.concat([fs.readFileSync(htmlPath), ...this._trailer()]),
        { level: 9 },
      );
      const tmpOut = this._tmpName(uid);
      fs.writeFileSync(tmpOut, gz);
      fs.renameSync(tmpOut, this._name(uid)); // atomic: no half-served artifact
      return { ok: true, bytes: gz.length, profile };
    } catch (ex) {
      return {
        ok: false,
        diagnostics: [],
        error: String(ex.message || ex).slice(0, 400),
      };
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true });
    }
  }

  has(uid) {
    return fs.existsSync(this._name(uid));
  }

  serve(res, uid, head = false) {
    // GET/HEAD path. Same gzip contract as before: store-time compression and
    // Content-Encoding on the way out, so the cheapest possible server hands
    // back ~200 KB per diagram. HEAD gets the same headers, no body.
    let payload;
    try {
      payload = fs.readFileSync(this._name(uid));
    } catch {
      return false;
    }
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Encoding": "gzip",
      "Content-Length": payload.length,
      "X-Content-Type-Options": "nosniff",
      // The artifact is rewritten under a new uid whenever the dashboard is
      // rebuilt, so a response may be cached for as long as a browser likes.
      "Cache-Control": "public, max-age=300",
    });
    res.end(head ? undefined : payload);
    return true;
  }

  list() {
    return fs
      .readdirSync(this.dir)
      .filter((name) => /^[0-9a-fA-F-]{8,40}\.html\.gz$/.test(name))
      .map((name) => name.replace(/\.html\.gz$/, ""))
      .filter((uid) => UID_RE.test(uid));
  }

  remove(uid) {
    // Every name an artifact could take, for a sweep that predates this
    // server. The .json is gone inside the container; the entry point knows
    // what it may have written.
    let removed = 0;
    for (const name of [`${uid}.html.gz`, `${uid}.html`, `${uid}.json`]) {
      const target = path.join(this.dir, name);
      try {
        if (fs.existsSync(target)) {
          fs.unlinkSync(target);
          removed += 1;
        }
      } catch {
        /* best effort: the sweep is idempotent, next round retries */
      }
    }
    return removed;
  }

  sweep(keep) {
    /**
     * Remove every artifact whose uid isn't in keep. The caller (RTMon)
     * owns which uids exist: its state files are the source of truth, and
     * it refuses to sweep on a partial answer. Here both the keep set and
     * the directory are given, so this is mechanical.
     */
    const kept = new Set(keep.map((u) => String(u)));
    let removed = 0;
    for (const uid of this.list()) {
      if (kept.has(uid)) continue;
      const target = this._name(uid);
      try {
        if (fs.existsSync(target)) {
          fs.unlinkSync(target);
          removed += 1;
        }
      } catch {
        /* idempotent; someone else may have already removed it */
      }
    }
    return removed;
  }
}

function createServer(config = {}) {
  const directory =
    config.diagramDir || process.env.ARCHIFY_DIAGRAM_DIR || "/srv/diagrams";
  const token =
    config.token !== undefined ? config.token : process.env.ARCHIFY_TOKEN || "";
  const cli =
    config.cli ||
    process.env.ARCHIFY_CLI ||
    path.join(__dirname, "archify-entry.mjs");
  const quality = config.quality || process.env.ARCHIFY_QUALITY || "standard";
  const chrome = config.chrome || process.env.ARCHIFY_CHROME || "hidden";
  const archive = new Archive(directory, cli, quality, chrome);

  function authorized(req) {
    if (!token) return null; // not configured: writers are closed, see main()
    const header = req.headers.authorization;
    if (!header || !header.startsWith("Bearer ")) return false;
    const given = Buffer.from(header.slice(7));
    const want = Buffer.from(token);
    return given.length === want.length && crypto.timingSafeEqual(given, want);
  }

  return http.createServer(async (req, res) => {
    const [pathname] = (req.url || "/").split("?", 1);
    const method = req.method || "GET";

    if (method === "GET" && pathname === "/healthz") {
      json(res, 200, { ok: true, version: VERSION, schemaVersion: 1 });
      return;
    }

    const uid = uidFromRequest(pathname);
    if (uid && (method === "GET" || method === "HEAD")) {
      if (!archive.serve(res, uid, method === "HEAD")) deny(res);
      return;
    }

    if (method === "POST" && pathname === "/v1/render") {
      const auth = authorized(req);
      if (auth === null) {
        json(res, 503, { ok: false, error: "service unavailable" });
        return;
      }
      if (auth === false) {
        json(res, 401, { ok: false, error: "unauthorized" });
        return;
      }
      let body;
      try {
        body = JSON.parse((await readBody(req, BODY_LIMIT)).toString("utf8"));
      } catch (ex) {
        json(res, 400, { ok: false, error: ex.message });
        return;
      }
      const { uid: wanted, ir } = body || {};
      if (!wanted || !UID_RE.test(String(wanted))) {
        json(res, 400, { ok: false, error: "a uid is required" });
        return;
      }
      if (!ir || typeof ir !== "object") {
        json(res, 400, {
          ok: false,
          error: "the ir is required and must be an object",
        });
        return;
      }
      const result = archive.render(String(wanted), ir, body.quality);
      if (result.ok) {
        json(res, 201, {
          ok: true,
          uid: String(wanted),
          bytes: result.bytes,
          profile: result.profile,
        });
        return;
      }
      json(res, result.diagnostics.length ? 422 : 500, {
        ok: false,
        ...result,
      });
      return;
    }

    if (method === "GET" && pathname === "/api/v1/artifacts") {
      const auth = authorized(req);
      if (auth === null) {
        json(res, 503, { ok: false, error: "service unavailable" });
        return;
      }
      if (auth === false) {
        json(res, 401, { ok: false, error: "unauthorized" });
        return;
      }
      json(res, 200, { ok: true, uids: archive.list() });
      return;
    }

    if (method === "POST" && pathname === "/api/v1/sweep") {
      const auth = authorized(req);
      if (auth === null) {
        json(res, 503, { ok: false, error: "service unavailable" });
        return;
      }
      if (auth === false) {
        json(res, 401, { ok: false, error: "unauthorized" });
        return;
      }
      let body;
      try {
        body = JSON.parse((await readBody(req, BODY_LIMIT)).toString("utf8"));
      } catch (ex) {
        json(res, 400, { ok: false, error: ex.message });
        return;
      }
      const keep = Array.isArray(body?.keep)
        ? body.keep.filter((u) => UID_RE.test(String(u)))
        : [];
      const removed = archive.sweep(keep);
      json(res, 200, { ok: true, removed });
      return;
    }

    const del = /^\/api\/v1\/artifacts\/([0-9a-fA-F-]{8,40})$/.exec(pathname);
    if (method === "DELETE" && del) {
      const auth = authorized(req);
      if (auth === null) {
        json(res, 503, { ok: false, error: "service unavailable" });
        return;
      }
      if (auth === false) {
        json(res, 401, { ok: false, error: "unauthorized" });
        return;
      }
      const removed = archive.remove(del[1]);
      json(res, 200, { ok: true, removed });
      return;
    }

    deny(res);
  });
}

function main() {
  // 8081, not 8080: RTMon's own results API (RTMon-Http, http_api_port)
  // defaults to 8080, and a sidecar shares the pod's network namespace with
  // it, so the two cannot both have that port.
  const port = Number(process.env.ARCHIFY_PORT || 8081);
  const bind = process.env.ARCHIFY_BIND || "0.0.0.0";
  const token = process.env.ARCHIFY_TOKEN || "";
  const server = createServer({});
  if (!token) {
    console.warn(
      "rtmon-archify: ARCHIFY_TOKEN is not set; render/list/delete are disabled " +
        "and only GET /diagrams/<uid>.html is served. Set the same token in " +
        "rtmon.yaml archify.token.",
    );
  }
  server.listen(port, bind, () => {
    console.log(
      `rtmon-archify sidecar on http://${bind}:${port} (archify ${VERSION})`,
    );
  });
}

const isMain =
  process.argv[1] &&
  fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isMain) {
  main();
}

export { ATTRIBUTION, Archive, UID_RE, createServer };
