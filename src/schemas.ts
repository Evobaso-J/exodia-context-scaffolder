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
export const L3_FILENAME_RE = /^[a-z][a-z0-9_-]*(?:\/[a-z][a-z0-9_-]*)*\.(yaml|jsonl|md)$/;
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
