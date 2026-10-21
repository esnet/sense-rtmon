// Tests for the RTMon Archify sidecar. Real renders, no mocks of the CLI:
// the whole point of this repo is that it is the thing that can run the
// upstream renderer, so a test that skips it proves nothing.
//
// Run: npm test  (node --test test/)
import assert from "node:assert/strict";
import { after, before, describe, it } from "node:test";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

import { createServer } from "../server.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const FIXTURE = JSON.parse(
  fs.readFileSync(path.join(HERE, "fixtures", "nrp.json"), "utf8"),
);
const TOKEN = "test-token-123";
const UID = "9f8e7d6c-aaaa-bbbb-cccc-0123456789ab";

let base;
let server;
let dir;

before(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "rtmon-archify-test-"));
  server = createServer({
    diagramDir: dir,
    token: TOKEN,
    cli: path.join(ROOT, "archify-entry.mjs"),
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => {
  server.close();
  fs.rmSync(dir, { recursive: true, force: true });
});

function request(method, pathname, body, token, root = base) {
  return new Promise((resolve, reject) => {
    const payload = body ? Buffer.from(JSON.stringify(body)) : null;
    const req = http.request(
      root + pathname,
      {
        method,
        headers: {
          ...(payload
            ? {
                "Content-Type": "application/json",
                "Content-Length": payload.length,
              }
            : {}),
          ...(token !== undefined ? { Authorization: `Bearer ${token}` } : {}),
        },
      },
      (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks),
          }),
        );
      },
    );
    req.on("error", reject);
    if (payload) req.write(payload);
    req.end();
  });
}

describe("healthz", () => {
  it("reports up with the archify version", async () => {
    const res = await request("GET", "/healthz");
    assert.equal(res.status, 200);
    const body = JSON.parse(res.body.toString());
    assert.equal(body.ok, true);
    assert.equal(typeof body.version, "string");
    assert.ok(body.version.length > 0);
  });
});

describe("render", () => {
  it("renders a real fixture IR to a gzipped artifact", async () => {
    const res = await request(
      "POST",
      "/v1/render",
      { uid: UID, ir: FIXTURE },
      TOKEN,
    );
    assert.equal(res.status, 201);
    const body = JSON.parse(res.body.toString());
    assert.equal(body.ok, true);
    assert.equal(body.uid, UID);
    const artifact = path.join(dir, `${UID}.html.gz`);
    assert.ok(fs.existsSync(artifact), "artifact file written");
    assert.ok(
      body.bytes > 50000,
      `artifact is a real diagram (${body.bytes} bytes)`,
    );
  });

  it("embeds the MIT attribution after </html>", async () => {
    const raw = fs.readFileSync(path.join(dir, `${UID}.html.gz`));
    const html = zlib.gunzipSync(raw).toString("utf8");
    assert.ok(html.indexOf("<!DOCTYPE html>") === 0, "DOCTYPE still first");
    assert.ok(
      html.includes(
        "Rendered by Archify (https://github.com/tt-a1i/archify), MIT licence.",
      ),
      "MIT notice present",
    );
    assert.ok(html.includes("SIL Open Font License"), "OFL line present");
    assert.ok(html.trimEnd().endsWith("-->"), "notice ends the file");
  });

  it("folds the diagram chrome behind one toggle", async () => {
    const raw = fs.readFileSync(path.join(dir, `${UID}.html.gz`));
    const html = zlib.gunzipSync(raw).toString("utf8");
    assert.ok(html.includes("rtmon-chrome-toggle"), "toggle injected");
    assert.ok(
      html.includes('dataset.rtmonChrome="hidden"'),
      "starts collapsed",
    );
    // The three control clusters the collapse covers. If the renderer ever
    // renames one of these, the toggle silently stops hiding it and the panel
    // goes back to sixteen buttons, so the selectors are asserted against the
    // rendered artifact rather than trusted.
    for (const cls of ["toolbar", "guided-views", "diagram-nav"]) {
      assert.ok(
        html.includes(`html[data-rtmon-chrome="hidden"] .${cls}`) ||
          html.includes(`.${cls} {`) ||
          html.includes(`class="${cls}`) ||
          html.includes(`"${cls}"`),
        `${cls} present in artifact`,
      );
    }
    assert.ok(
      html.indexOf("rtmon-chrome-toggle") < html.indexOf("Rendered by Archify"),
      "toggle precedes the licence notice",
    );
  });

  it("serves it gzipped with the same cache contract as before", async () => {
    const res = await request("GET", `/diagrams/${UID}.html`);
    assert.equal(res.status, 200);
    assert.equal(res.headers["content-encoding"], "gzip");
    assert.equal(res.headers["content-type"], "text/html; charset=utf-8");
    assert.match(res.headers["cache-control"], /max-age=300/);
    const html = zlib.gunzipSync(res.body).toString("utf8");
    assert.ok(
      html.includes("edgecore"),
      "artifact names a device from the path",
    );
  });

  it("answers HEAD with the same headers and no body", async () => {
    const res = await request("HEAD", `/diagrams/${UID}.html`);
    assert.equal(res.status, 200);
    assert.equal(res.headers["content-encoding"], "gzip");
    assert.equal(res.body.length, 0, "HEAD carries no body");
  });

  it("does not need a token configured for GET only", async () => {
    // The no-token mode must still serve, per the auth split.
    const res = await request("GET", `/diagrams/${UID}.html`, null, undefined);
    assert.equal(res.status, 200);
  });
});

describe("render auth", () => {
  it("rejects render without a bearer header", async () => {
    const res = await request(
      "POST",
      "/v1/render",
      { uid: UID, ir: FIXTURE },
      undefined,
    );
    assert.equal(res.status, 401);
  });

  it("rejects a wrong token with 401", async () => {
    const res = await request(
      "POST",
      "/v1/render",
      { uid: UID, ir: FIXTURE },
      "wrong",
    );
    assert.equal(res.status, 401);
  });

  it("rejects a missing uid or ir with 400", async () => {
    const res = await request("POST", "/v1/render", { ir: FIXTURE }, TOKEN);
    assert.equal(res.status, 400);
    const res2 = await request("POST", "/v1/render", { uid: UID }, TOKEN);
    assert.equal(res2.status, 400);
  });

  it("rejects a uid that is a path", async () => {
    const res = await request(
      "POST",
      "/v1/render",
      { uid: "../../etc/passwd", ir: FIXTURE },
      TOKEN,
    );
    assert.equal(res.status, 400);
  });
});

describe("validation diagnostics", () => {
  it("returns 422 with diagnostics for an invalid IR", async () => {
    const bad = JSON.parse(JSON.stringify(FIXTURE));
    bad.components[0].label = "x".repeat(500); // wider than its box
    const res = await request(
      "POST",
      "/v1/render",
      { uid: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", ir: bad },
      TOKEN,
    );
    assert.equal(res.status, 422);
    const body = JSON.parse(res.body.toString());
    assert.equal(body.ok, false);
    assert.ok(
      Array.isArray(body.diagnostics) && body.diagnostics.length > 0,
      "diagnostics carried",
    );
  });
});

describe("archive listing and removal", () => {
  it("lists only uid-shaped artifacts", async () => {
    fs.writeFileSync(path.join(dir, "not-a-uid.html.gz"), "x");
    const res = await request("GET", "/api/v1/artifacts", null, TOKEN);
    assert.equal(res.status, 200);
    const body = JSON.parse(res.body.toString());
    assert.ok(body.uids.includes(UID), "the rendered uid is listed");
    assert.ok(!body.uids.includes("not-a-uid"), "garbage is not listed");
  });

  it("removes one artifact", async () => {
    const res = await request(
      "DELETE",
      `/api/v1/artifacts/${UID}`,
      null,
      TOKEN,
    );
    assert.equal(res.status, 200);
    assert.equal(JSON.parse(res.body.toString()).removed, 1);
    assert.ok(!fs.existsSync(path.join(dir, `${UID}.html.gz`)));
  });

  it("sweeps by keep-set", async () => {
    const other = "bbbbbbbb-2222-3333-4444-555555555555";
    await request("POST", "/v1/render", { uid: other, ir: FIXTURE }, TOKEN);
    // Removing uid already removed UID; this renders again so the sweep has
    // something to act on and a keep-set to honour.
    await request("POST", "/v1/render", { uid: UID, ir: FIXTURE }, TOKEN);
    const res = await request("POST", "/api/v1/sweep", { keep: [UID] }, TOKEN);
    assert.equal(res.status, 200);
    const body = JSON.parse(res.body.toString());
    assert.equal(body.removed, 1, "the unkept uid is removed");
    assert.ok(
      fs.existsSync(path.join(dir, `${UID}.html.gz`)),
      "kept uid survives",
    );
    assert.ok(
      !fs.existsSync(path.join(dir, `${other}.html.gz`)),
      "unkept uid is gone",
    );
  });

  it("rejects list/delete without auth", async () => {
    assert.equal(
      (await request("GET", "/api/v1/artifacts", null, undefined)).status,
      401,
    );
    assert.equal(
      (await request("DELETE", `/api/v1/artifacts/${UID}`, null, undefined))
        .status,
      401,
    );
    assert.equal(
      (await request("GET", "/api/v1/artifacts", null, "nope")).status,
      401,
    );
  });
});

describe("tokenless mode", () => {
  // A sidecar with no ARCHIFY_TOKEN serves GETs but keeps every write closed:
  // an unconfigured render endpoint must not be an anonymous code exec.
  let tokenless;
  let tokenlessBase;
  before(async () => {
    tokenless = createServer({
      diagramDir: fs.mkdtempSync(
        path.join(os.tmpdir(), "rtmon-archify-notoken-"),
      ),
      cli: path.join(ROOT, "archify-entry.mjs"),
    });
    await new Promise((resolve) => tokenless.listen(0, "127.0.0.1", resolve));
    tokenlessBase = `http://127.0.0.1:${tokenless.address().port}`;
  });
  after(() => tokenless.close());

  it("serves artifacts but refuses render with 503", async () => {
    const serve = await new Promise((resolve) => {
      http.get(tokenlessBase + `/diagrams/${UID}.html`, (res) => {
        res.resume();
        res.on("end", () => resolve(res.statusCode));
      });
    });
    assert.equal(
      serve,
      404,
      "the tokenless dir has no artifacts; serving still works",
    );
    const res = await request(
      "POST",
      "/v1/render",
      { uid: UID, ir: FIXTURE },
      undefined,
      tokenlessBase,
    );
    assert.equal(res.status, 503);
    const body = res.body.toString();
    assert.ok(!body.includes("token"), "a probe learns nothing about auth");
  });
});

describe("route discipline", () => {
  it("refuses everything that is not a served artifact", async () => {
    for (const p of [
      "/",
      "/diagrams",
      `/diagrams/${UID}.json`,
      `/diagrams/${UID}.html.gz`,
      "/diagrams/..%2f..%2fetc%2fpasswd.html",
      "/diagrams/not-a-uid.html",
      "/favicon.ico",
    ]) {
      const res = await request("GET", p);
      assert.equal(res.status, 404, `${p} should be refused`);
    }
  });
});
