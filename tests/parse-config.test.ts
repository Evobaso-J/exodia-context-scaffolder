import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const REPO = resolve(__dirname, "..");
const CLI = join(REPO, "dist", "parse-config.mjs");
const FIXTURES = join(REPO, "tests", "fixtures");

function runCli(args: string[]): { stdout: string; status: number } {
  try {
    const stdout = execFileSync("node", [CLI, ...args], { encoding: "utf-8" });
    return { stdout, status: 0 };
  } catch (e) {
    const err = e as { stdout?: Buffer | string; status?: number };
    return { stdout: typeof err.stdout === "string" ? err.stdout : err.stdout?.toString() ?? "", status: err.status ?? 1 };
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

  it("exits 66 when the path is missing", () => {
    const { status } = runCli([join(REPO, "examples", "does-not-exist.yaml")]);
    expect(status).toBe(66);
  });
});
