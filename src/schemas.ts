import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

/**
 * Symlink-tolerant entrypoint check. When the skill dir is a symlink (e.g.
 * brain-sync links personal skills into ~/.claude/skills), Node resolves
 * import.meta.url to the script's realpath while process.argv[1] keeps the
 * symlink path, so a strict href comparison fails and main() silently never
 * runs. Canonicalize both sides with realpathSync before comparing.
 */
export function isEntrypoint(importMetaUrl: string, entry: string | undefined): boolean {
  if (!entry) return false;
  try {
    return realpathSync(fileURLToPath(importMetaUrl)) === realpathSync(entry);
  } catch {
    return false;
  }
}

export const CANONICAL_CATEGORIES = [
  "architecture",
  "design-patterns",
  "glossary",
  "operations",
  "debugging",
] as const;

export const RECOGNIZED_CATEGORIES: ReadonlySet<string> = new Set(CANONICAL_CATEGORIES);

export const PATH_RE = /^[a-z._-][a-z0-9._/-]*$/;
export const CATEGORY_NAME_RE = /^[a-z][a-z0-9_-]*$/;
// A trailing `/` marks an entry directory: one file per entry, no shared file.
// `.jsonl` is deliberately absent: a shared append-only file puts every branch on
// the same tail line, so parallel branches conflict on every merge.
export const L3_FILENAME_RE = /^[a-z][a-z0-9_-]*(?:\/[a-z][a-z0-9_-]*)*(?:\.(yaml|md)|\/)$/;
export const DESCRIPTION_MAX_LEN = 200;

export type ResolvedCategory = {
  name: string;
  path: string | null;
  kind: "canonical" | "custom";
  l3_override: string[] | null;
  description: string | null;
  drop: boolean;
};

export type ParseConfigOutput = {
  context_dir: string;
  categories: ResolvedCategory[];
};

export type L3Spec = {
  filename: string;
  schema_name: string | null;
  schema_template_path: string | null;
};

export type ResolvedLayoutEntry = {
  name: string;
  path: string;
  kind: "canonical" | "custom";
  description: string | null;
  l2_template_path: string | null;
  l3_specs: L3Spec[] | null;
};

export type LedgerCandidate = { host: string; schema: string };
export type LedgerRegistry = Map<string, LedgerCandidate[]>;
