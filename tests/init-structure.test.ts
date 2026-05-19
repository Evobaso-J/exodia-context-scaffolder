import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

const REPO = resolve(__dirname, "..");
const CLI = join(REPO, "dist", "init-structure.mjs");

function walk(root: string): string[] {
  const out: string[] = [];
  function recurse(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        out.push(relative(root, full) + "/");
        recurse(full);
      } else {
        out.push(relative(root, full));
      }
    }
  }
  recurse(root);
  return out.sort();
}

describe("init-structure", () => {
  let tmp: string;

  beforeEach(() => {
    tmp = mkdtempSync(join(tmpdir(), "exodia-test-"));
  });

  afterEach(() => {
    rmSync(tmp, { recursive: true, force: true });
  });

  it("legacy mode: creates context dir and copies canonical templates", () => {
    execFileSync("node", [
      CLI,
      tmp,
      "context",
      "architecture",
      "design-patterns",
      "operations",
      "debugging",
      "glossary",
    ]);

    const files = walk(tmp);
    expect(files).toContain("context/");
    expect(files).toContain("context/architecture/ARCHITECTURE.md");
    expect(files).toContain("context/architecture/decisions.jsonl");
    expect(files).toContain("context/design-patterns/DESIGN-PATTERNS.md");
    expect(files).toContain("context/design-patterns/reviews.jsonl");
    expect(files).toContain("context/design-patterns/docs/");
    expect(files).toContain("context/design-patterns/docs/.gitkeep");
    expect(files).toContain("context/glossary/GLOSSARY.md");
    expect(files).toContain("context/glossary/glossary.yaml");
  });

  it("--pairs mode: materializes each pair at its declared path", () => {
    execFileSync("node", [
      CLI,
      tmp,
      "--pairs",
      "architecture=docs/architecture",
      "glossary=docs/handbook/glossary",
      "mobile=docs/mobile",
    ]);

    expect(statSync(join(tmp, "docs/architecture/ARCHITECTURE.md")).isFile()).toBe(true);
    expect(statSync(join(tmp, "docs/handbook/glossary/glossary.yaml")).isFile()).toBe(true);
    expect(statSync(join(tmp, "docs/mobile/MOBILE.md")).isFile()).toBe(true);

    const stub = readFileSync(join(tmp, "docs/mobile/MOBILE.md"), "utf-8");
    expect(stub).toContain("# MOBILE");
    expect(stub).toContain("<!-- exodia:section:intro -->");
    expect(stub).toContain("<!-- exodia:section:purpose -->");
  });

  it("never overwrites existing destination files", () => {
    execFileSync("node", [CLI, tmp, "--pairs", "mobile=docs/mobile"]);
    const stubPath = join(tmp, "docs/mobile/MOBILE.md");
    const original = readFileSync(stubPath, "utf-8");

    execFileSync("node", [CLI, tmp, "--pairs", "mobile=docs/mobile"]);
    expect(readFileSync(stubPath, "utf-8")).toBe(original);
  });

  it("rejects malformed --pairs", () => {
    expect(() => {
      execFileSync("node", [CLI, tmp, "--pairs", "no-equals-sign"], { stdio: "pipe" });
    }).toThrow();
  });

  it("rejects an invalid context_dir name", () => {
    expect(() => {
      execFileSync("node", [CLI, tmp, "..", "architecture"], { stdio: "pipe" });
    }).toThrow();
  });
});
