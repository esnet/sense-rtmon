#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// The vendored subset sits beside this file, not above it: upstream's entry
// point lived in archify-cli/bin, this one is ours, so archify-cli/ stays a
// tree of unmodified upstream files. See README's vendoring section.
const skillRoot = path.join(__dirname, "archify-cli");

const TYPES = new Set(["architecture"]);

function usage() {
  return `Usage:
  archify render architecture <input.json> [output.html] [--quality standard|showcase] [--repo-root path]
  archify validate architecture <input.json> [--json] [--layout-json] [--quality standard|showcase] [--repo-root path]

This is the RTMon build of archify: the two subcommands the rtmon-archify
sidecar calls, and the one diagram type RTMon emits. The upstream tool's
other subcommands and diagram types are not shipped here - see README.md.
`;
}

function fail(message, code = 2) {
  console.error(message);
  process.exit(code);
}

function rejectCliArgument(message, details = {}) {
  const error = new Error(message);
  error.archifyArgument = {
    code: details.code || "cli/invalid-arguments",
    subject: details.subject || {},
    evidence: details.evidence || {},
    supportedFixes: details.supportedFixes || [
      "correct the command arguments and retry",
    ],
  };
  throw error;
}

function rendererPath(type) {
  if (!TYPES.has(type)) {
    rejectCliArgument(
      `Unknown diagram type "${type}". Expected one of: ${[...TYPES].join(", ")}`,
      {
        code: "cli/unknown-diagram-type",
        subject: { type },
        evidence: { supportedTypes: [...TYPES] },
        supportedFixes: [`use one of: ${[...TYPES].join(", ")}`],
      },
    );
  }
  return path.join(skillRoot, "renderers", type, `render-${type}.mjs`);
}

function runNode(args, options = {}) {
  return spawnSync(process.execPath, args, {
    cwd: options.cwd || process.cwd(),
    encoding: "utf8",
    stdio: options.stdio || "inherit",
    env: options.env ? { ...process.env, ...options.env } : process.env,
  });
}

function extractQualityArgs(args) {
  const rest = [];
  let quality;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--quality") {
      quality = args[index + 1];
      if (!quality || quality.startsWith("--"))
        rejectCliArgument("--quality requires standard or showcase.", {
          code: "cli/missing-option-value",
          subject: { option: "--quality" },
          supportedFixes: ["provide --quality standard or --quality showcase"],
        });
      index += 1;
      continue;
    }
    if (arg.startsWith("--quality=")) {
      quality = arg.slice("--quality=".length);
      if (!quality)
        rejectCliArgument("--quality requires standard or showcase.", {
          code: "cli/missing-option-value",
          subject: { option: "--quality" },
          supportedFixes: ["provide --quality standard or --quality showcase"],
        });
      continue;
    }
    rest.push(arg);
  }
  if (quality !== undefined && !["standard", "showcase"].includes(quality)) {
    rejectCliArgument(
      `Unknown quality profile "${quality}". Expected standard or showcase.`,
      {
        code: "cli/invalid-option-value",
        subject: { option: "--quality" },
        evidence: { value: quality, supportedValues: ["standard", "showcase"] },
        supportedFixes: ["use --quality standard or --quality showcase"],
      },
    );
  }
  return { rest, quality };
}

function extractRepoRootArgs(args) {
  const rest = [];
  let repoRoot;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--repo-root") {
      repoRoot = args[index + 1];
      if (!repoRoot || repoRoot.startsWith("--"))
        rejectCliArgument("--repo-root requires a repository path.", {
          code: "cli/missing-option-value",
          subject: { option: "--repo-root" },
          supportedFixes: ["provide one repository path after --repo-root"],
        });
      index += 1;
      continue;
    }
    if (arg.startsWith("--repo-root=")) {
      repoRoot = arg.slice("--repo-root=".length);
      if (!repoRoot)
        rejectCliArgument("--repo-root requires a repository path.", {
          code: "cli/missing-option-value",
          subject: { option: "--repo-root" },
          supportedFixes: ["provide one repository path after --repo-root"],
        });
      continue;
    }
    rest.push(arg);
  }
  return { rest, repoRoot: repoRoot ? path.resolve(repoRoot) : undefined };
}

function rendererEnv(quality, repoRoot, diagnosticJson = false) {
  return {
    ...(quality ? { ARCHIFY_QUALITY_PROFILE: quality } : {}),
    ...(repoRoot ? { ARCHIFY_REPO_ROOT: repoRoot } : {}),
    ...(diagnosticJson ? { ARCHIFY_DIAGNOSTIC_FORMAT: "json" } : {}),
  };
}

function diagnostic({
  code,
  message,
  subject = {},
  evidence = {},
  supportedFixes = [],
  severity = "error",
}) {
  return {
    code,
    severity,
    message,
    subject,
    evidence,
    supportedFixes,
  };
}

function rendererFailure(result) {
  if (result.error) {
    return {
      error: "Renderer process could not start.",
      diagnostics: [
        diagnostic({
          code: "internal/renderer-process",
          message: "Renderer process could not start.",
          evidence: { reason: result.error.message },
        }),
      ],
    };
  }
  try {
    const payload = JSON.parse((result.stderr || "").trim());
    if (
      payload?.ok === false &&
      Array.isArray(payload.diagnostics) &&
      payload.diagnostics.length
    ) {
      return {
        error: payload.error || payload.diagnostics[0].message,
        diagnostics: payload.diagnostics,
      };
    }
  } catch {
    // The diagnostic boundary is intentionally fail-closed. Never copy a raw
    // Node stack into a machine receipt when a renderer exits unexpectedly.
  }
  return {
    error: "Renderer failed before emitting a structured diagnostic.",
    diagnostics: [
      diagnostic({
        code: "internal/unclassified",
        message: "Renderer failed before emitting a structured diagnostic.",
        evidence: { exitCode: result.status ?? 1 },
      }),
    ],
  };
}

const COMPOSITION_CHECKS = new Set([
  "label_route_clearance",
  "relationship_crossings",
  "relationship_corridors",
  "container_border_runs",
  "route_rhythm",
]);

const CHECK_FIXES = {
  single_svg: [
    "remove additional SVG roots so the artifact contains exactly one diagram SVG",
  ],
  finite_svg: ["replace non-finite coordinates before rendering again"],
  orthogonal_arrows: ["use renderer-supported orthogonal routing controls"],
  legend_clearance: [
    "move the route or enlarge the viewBox so relationships do not enter the legend",
  ],
};

const COMPOSITION_FIXES = {
  "composition/proper-crossing": [
    "adjust route/via or channel coordinates so unrelated relationships use separate corridors",
  ],
  "composition/ambiguous-corridor": [
    "adjust route/via or channel coordinates so unrelated relationships do not visually merge",
  ],
  "composition/container-border-run": [
    "route across the frame perpendicularly through a clear opening",
  ],
  "composition/label-route-clearance": [
    "adjust labelAt, labelDx, labelDy, labelSegment, message y, or the other relationship route",
  ],
  "composition/desktop-readability": [
    "reduce the viewBox width, shorten node copy, widen affected nodes, or split the diagram so node context remains at least 6px at a 1440px desktop viewport",
  ],
  "composition/micro-segment": [
    "move the route/channel/via point so every visible segment is at least 8px",
  ],
  "composition/short-interior-segment": [
    "move the route/channel/via point so every interior turn has at least 16px",
  ],
};

function checkerDiagnostics(checker) {
  const diagnostics = [];
  for (const issue of checker?.composition?.issues || []) {
    if (issue.severity !== "error") continue;
    const { severity, code, relationship, ...evidence } = issue;
    diagnostics.push(
      diagnostic({
        code,
        severity,
        message: `Final artifact failed ${code}.`,
        subject: relationship ? { relationship } : { check: "composition" },
        evidence,
        supportedFixes: COMPOSITION_FIXES[code] || [],
      }),
    );
  }
  for (const check of checker?.checks || []) {
    if (check.ok || COMPOSITION_CHECKS.has(check.name)) continue;
    diagnostics.push(
      diagnostic({
        code: `artifact/${check.name.replaceAll("_", "-")}`,
        message:
          (check.details || []).find(Boolean) ||
          `Final artifact failed ${check.name}.`,
        subject: { check: check.name },
        evidence: { details: check.details || [] },
        supportedFixes: CHECK_FIXES[check.name] || [],
      }),
    );
  }
  return diagnostics.length
    ? diagnostics
    : [
        diagnostic({
          code: "artifact/check-failed",
          message:
            "Final artifact check failed without a classified diagnostic.",
          subject: { check: "unknown" },
          evidence: {},
        }),
      ];
}

function formatDiagnostics(error, diagnostics = []) {
  if (!diagnostics.length) return error;
  return [
    error,
    ...diagnostics.map((entry) => {
      const fix = entry.supportedFixes?.length
        ? ` Fix: ${entry.supportedFixes.join("; ")}.`
        : "";
      return `[${entry.code}] ${entry.message}${fix}`;
    }),
  ].join("\n");
}

function assertEvidenceType(type, repoRoot) {
  if (repoRoot && type !== "architecture") {
    rejectCliArgument(
      "--repo-root is currently supported for architecture diagrams only.",
      {
        code: "cli/unsupported-option",
        subject: { option: "--repo-root", type },
        supportedFixes: ["remove --repo-root or use an architecture diagram"],
      },
    );
  }
}

function exitFrom(result) {
  if (result.error) fail(result.error.message, 1);
  process.exit(result.status ?? 1);
}

function commandRender(args) {
  const qualityArgs = extractQualityArgs(args);
  const repoArgs = extractRepoRootArgs(qualityArgs.rest);
  // render takes no options of its own once --quality and --repo-root are
  // stripped, so anything left starting with -- is a typo. Without this a
  // mistyped flag was taken as the output path: `render architecture spec.json
  // --json out.html` wrote a file literally named `--json` and never wrote
  // out.html, exiting 0. Every sibling subcommand already guards this.
  const unknown = repoArgs.rest.filter((arg) => arg.startsWith("--"));
  if (unknown.length) fail(`Unknown render option "${unknown[0]}".`);
  const [type, input, output] = repoArgs.rest;
  if (!type || !input || repoArgs.rest.length > 3) fail(usage());
  assertEvidenceType(type, repoArgs.repoRoot);
  const result = runNode(
    [rendererPath(type), input, ...(output ? [output] : [])],
    {
      env: rendererEnv(qualityArgs.quality, repoArgs.repoRoot),
    },
  );
  if (result.status !== 0) exitFrom(result);
}

function reportArtifactFailure({
  command,
  json,
  stage,
  type,
  input,
  output,
  error,
  diagnostics = [],
  status = 1,
  checker,
}) {
  const receipt = {
    schemaVersion: 1,
    ok: false,
    command,
    stage,
    type,
    input,
    ...(output === undefined ? {} : { output }),
    error,
    diagnostics,
    ...(checker ? { checker } : {}),
  };
  if (json) console.log(JSON.stringify(receipt, null, 2));
  else console.error(formatDiagnostics(error, diagnostics));
  process.exitCode = status;
}

function reportValidateFailure(options) {
  reportArtifactFailure({ ...options, command: "validate" });
}

function reportArtifactArgumentFailure(command, error) {
  const details = error.archifyArgument || {};
  reportArtifactFailure({
    command,
    json: true,
    stage: "arguments",
    error: error.message,
    diagnostics: [
      diagnostic({
        code: details.code || "cli/invalid-arguments",
        message: error.message,
        subject: { command, ...(details.subject || {}) },
        evidence: details.evidence || {},
        supportedFixes: details.supportedFixes || [
          "correct the command arguments and retry",
        ],
      }),
    ],
    status: 2,
  });
}

function engineeringProfileFromArtifact(artifact) {
  const match = artifact
    .toString("utf8")
    .match(/<svg[^>]*\sdata-engineering-profile="([^"]+)"/);
  return match ? match[1] : null;
}

function commandValidate(args) {
  const qualityArgs = extractQualityArgs(args);
  const repoArgs = extractRepoRootArgs(qualityArgs.rest);
  args = repoArgs.rest;
  const quality = qualityArgs.quality;
  const repoRoot = repoArgs.repoRoot;
  const knownOptions = new Set(["--json", "--layout-json"]);
  const unknown = args.filter(
    (arg) => arg.startsWith("--") && !knownOptions.has(arg),
  );
  if (unknown.length)
    rejectCliArgument(`Unknown validate option "${unknown[0]}".`, {
      code: "cli/unknown-option",
      subject: { option: unknown[0] },
      supportedFixes: ["remove the unknown option and retry"],
    });
  const json = args.includes("--json");
  const layoutJson = args.includes("--layout-json");
  const rest = args.filter((arg) => !knownOptions.has(arg));
  const [type, input] = rest;
  if (!type || !input || rest.length !== 2)
    rejectCliArgument(usage(), {
      code: "cli/usage",
      supportedFixes: ["use: archify validate <type> <input.json> [options]"],
    });
  assertEvidenceType(type, repoRoot);
  const renderer = rendererPath(type);

  if (layoutJson && !["architecture", "workflow"].includes(type)) {
    rejectCliArgument(
      "--layout-json is currently supported for architecture and workflow diagrams only.",
      {
        code: "cli/unsupported-option",
        subject: { option: "--layout-json", type },
        supportedFixes: [
          "remove --layout-json or use an architecture or workflow diagram",
        ],
      },
    );
  }

  if (layoutJson) {
    // Layout mode emits JSON without writing HTML; keep its unused target typed.
    const layoutOutput = path.join(
      os.tmpdir(),
      `archify-layout-${process.pid}-${type}.html`,
    );
    const result = runNode([renderer, input, layoutOutput, "--layout-json"], {
      stdio: "pipe",
      env: rendererEnv(quality, repoRoot, true),
    });
    if (result.status !== 0) {
      try {
        const receipt = JSON.parse(result.stdout);
        if (receipt?.contract && Array.isArray(receipt.diagnostics)) {
          process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
          process.exitCode = result.status ?? 1;
          return;
        }
      } catch {
        // Fall through to the renderer failure contract when no compiler
        // receipt was produced (for example, input JSON could not be read).
      }
      const failure = rendererFailure(result);
      reportValidateFailure({
        json,
        stage: failure.diagnostics.some((entry) =>
          entry.code.startsWith("input/"),
        )
          ? "input"
          : "render",
        type,
        input: path.resolve(input),
        error: failure.error,
        diagnostics: failure.diagnostics,
        status: result.status ?? 1,
      });
      return;
    }
    process.stdout.write(result.stdout);
    return;
  }

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "archify-validate-"));
  const out = path.join(tmp, `${type}.html`);
  let exitCode = 0;

  try {
    const render = runNode([renderer, input, out], {
      stdio: "pipe",
      env: rendererEnv(quality, repoRoot, true),
    });
    if (render.status !== 0) {
      const failure = rendererFailure(render);
      reportValidateFailure({
        json,
        stage: failure.diagnostics.some((entry) =>
          entry.code.startsWith("input/"),
        )
          ? "input"
          : "render",
        type,
        input: path.resolve(input),
        error: failure.error,
        diagnostics: failure.diagnostics,
        status: render.status ?? 1,
      });
      exitCode = render.status ?? 1;
    } else {
      const check = runNode(
        [path.join(skillRoot, "scripts/check-render-output.mjs"), out],
        { stdio: "pipe" },
      );
      if (check.status !== 0) {
        let checker;
        try {
          checker = JSON.parse(check.stdout);
          checker.file = path.resolve(input);
        } catch {
          checker = {
            ok: false,
            diagnostic: "Artifact checker failed without a parseable receipt.",
          };
        }
        reportValidateFailure({
          json,
          stage: "check",
          type,
          input: path.resolve(input),
          error: "Final artifact check failed.",
          diagnostics: checkerDiagnostics(checker),
          checker,
          status: check.status ?? 1,
        });
        exitCode = check.status ?? 1;
      } else {
        const result = JSON.parse(check.stdout);
        const engineeringProfile = engineeringProfileFromArtifact(
          fs.readFileSync(out),
        );
        if (json) {
          console.log(
            JSON.stringify(
              {
                schemaVersion: 1,
                ok: true,
                command: "validate",
                type,
                input: path.resolve(input),
                checks: result.checks,
                composition: result.composition,
                ...(engineeringProfile ? { engineeringProfile } : {}),
              },
              null,
              2,
            ),
          );
        } else {
          const engineering = engineeringProfile
            ? `; engineering ${engineeringProfile}: pass`
            : "";
          console.log(
            `ok ${type} ${path.resolve(input)} (${result.checks.length} artifact checks; composition ${result.composition.profile}: ${result.composition.summary.errors} errors, ${result.composition.summary.warnings} warnings${engineering})`,
          );
        }
      }
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }

  if (exitCode !== 0) process.exitCode = exitCode;
}

const [command, ...args] = process.argv.slice(2);

try {
  switch (command) {
    case undefined:
    case "-h":
    case "--help":
    case "help":
      console.log(usage());
      break;
    case "render":
      commandRender(args);
      break;
    case "validate":
      commandValidate(args);
      break;
    case "inspect":
      commandValidate([...args, "--layout-json"]);
      break;
    default:
      fail(`Unknown command "${command}".\n\n${usage()}`);
  }
} catch (error) {
  if (!error.archifyArgument) throw error;
  if (command === "validate" && args.includes("--json")) {
    reportArtifactArgumentFailure(command, error);
  } else {
    fail(error.message);
  }
}
