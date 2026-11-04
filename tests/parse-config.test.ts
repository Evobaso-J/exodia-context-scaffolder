import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const REPO = resolve(__dirname, "..");
const CLI = join(REPO, "dist", "parse-config.mjs");
const FIXTURES = join(REPO, "tests", "fixtures");

function runCli(args: string[]): { stdout: string; stderr: string; status: number } {
  try {
    const stdout = execFileSync("node", [CLI, ...args], { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
    return { stdout, stderr: "", status: 0 };
  } catch (e) {
    const err = e as { stdout?: Buffer | string; stderr?: Buffer | string; status?: number };
    const text = (v: Buffer | string | undefined): string => (typeof v === "string" ? v : v?.toString() ?? "");
    return { stdout: text(err.stdout), stderr: text(err.stderr), status: err.status ?? 1 };
  }
}

describe("parse-config", () => {
  it("matches golden master for the full example config", () => {
    const { stdout, status } = runCli([join(REPO, "examples", "exodia.config.yaml")]);
    expect(status).toBe(0);
    const golden = readFileSync(join(FIXTURES, "parse-config.full.json"), "utf-8");
    expect(stdout).toBe(golden);
  });

  it("matches golden master for the minimal example config", () => {
    const { stdout, status } = runCli([join(REPO, "examples", "exodia.config.minimal.yaml")]);
    expect(status).toBe(0);
    const golden = readFileSync(join(FIXTURES, "parse-config.minimal.json"), "utf-8");
    expect(stdout).toBe(golden);
  });

  it("exits 64 when called without args", () => {
    const { status } = runCli([]);
    expect(status).toBe(64);
  });

  it("rejects a .jsonl ledger and names the entry-directory replacement", () => {
    const path = join(mkdtempSync(join(tmpdir(), "exodia-cfg-")), "exodia.config.yaml");
    writeFileSync(
      path,
      "categories:\n  mobile:\n    path: docs/mobile\n    custom: true\n    l3: [device_quirks.jsonl]\n",
    );
    const { status, stderr } = runCli([path]);
    expect(status).toBe(65);
    expect(stderr).toContain("device_quirks.jsonl");
    expect(stderr).toContain("device_quirks/");
  });

  it("exits 66 when the path is missing", () => {
    const { status } = runCli([join(REPO, "examples", "does-not-exist.yaml")]);
    expect(status).toBe(66);
  });
});
