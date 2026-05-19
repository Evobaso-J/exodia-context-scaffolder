import { execFileSync } from "node:child_process";
import { readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const REPO = resolve(__dirname, "..");
const PARSE_CLI = join(REPO, "dist", "parse-config.mjs");
const RESOLVE_CLI = join(REPO, "dist", "resolve-layout.mjs");
const FIXTURES = join(REPO, "tests", "fixtures");

function pipe(configPath: string): { stdout: string; status: number } {
  const parsed = execFileSync("node", [PARSE_CLI, configPath], { encoding: "utf-8" });
  try {
    const stdout = execFileSync("node", [RESOLVE_CLI, "--skill-dir", REPO], {
      input: parsed,
      encoding: "utf-8",
    });
    return { stdout, status: 0 };
  } catch (e) {
    const err = e as { stdout?: Buffer | string; status?: number };
    return { stdout: typeof err.stdout === "string" ? err.stdout : err.stdout?.toString() ?? "", status: err.status ?? 1 };
  }
}

describe("resolve-layout", () => {
  it("matches golden master for the full example config", () => {
    const { stdout, status } = pipe(join(REPO, "examples", "exodia.config.yaml"));
    expect(status).toBe(0);
    const golden = readFileSync(join(FIXTURES, "resolve-layout.full.json"), "utf-8");
    expect(stdout).toBe(golden);
  });

  it("matches golden master for the minimal example config", () => {
    const { stdout, status } = pipe(join(REPO, "examples", "exodia.config.minimal.yaml"));
    expect(status).toBe(0);
    const golden = readFileSync(join(FIXTURES, "resolve-layout.minimal.json"), "utf-8");
    expect(stdout).toBe(golden);
  });

  it("accepts --config in lieu of stdin", () => {
    const parsed = execFileSync("node", [PARSE_CLI, join(REPO, "examples", "exodia.config.yaml")], {
      encoding: "utf-8",
    });
    const tmp = join(REPO, "tests", "fixtures", "_parsed-temp.json");
    writeFileSync(tmp, parsed);
    try {
      const stdout = execFileSync("node", [RESOLVE_CLI, "--skill-dir", REPO, "--config", tmp], {
        encoding: "utf-8",
      });
      const golden = readFileSync(join(FIXTURES, "resolve-layout.full.json"), "utf-8");
      expect(stdout).toBe(golden);
    } finally {
      unlinkSync(tmp);
    }
  });
});
