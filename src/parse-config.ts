import { readFileSync, statSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { parse as parseYaml, YAMLParseError } from "yaml";

import {
  CANONICAL_CATEGORIES,
  CATEGORY_NAME_RE,
  DESCRIPTION_MAX_LEN,
  L3_FILENAME_RE,
  PATH_RE,
  RECOGNIZED_CATEGORIES,
  type ParseConfigOutput,
  type ResolvedCategory,
} from "./schemas.js";

const ALLOWED_TOP_LEVEL = new Set(["context_dir", "categories"]);
const ALLOWED_CATEGORY_FIELDS = new Set(["path", "drop", "custom", "l3", "description"]);

class ConfigError extends Error {
  line: number | undefined;
  constructor(message: string, line?: number) {
    super(message);
    this.line = line;
  }
}

class ConfigErrorList extends Error {
  readonly errors: ConfigError[];
  constructor(errors: ConfigError[]) {
    super(`${errors.length} validation error(s)`);
    this.errors = errors;
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function pythonRepr(value: unknown): string {
  if (value === null || value === undefined) return "None";
  if (typeof value === "string") return `'${value.replace(/'/g, "\\'")}'`;
  if (typeof value === "boolean") return value ? "True" : "False";
  return String(value);
}

function pythonListRepr(items: string[]): string {
  return `[${items.map((s) => `'${s}'`).join(", ")}]`;
}

function typeName(value: unknown): string {
  if (value === null) return "NoneType";
  if (Array.isArray(value)) return "list";
  if (typeof value === "boolean") return "bool";
  if (typeof value === "number") return Number.isInteger(value) ? "int" : "float";
  if (typeof value === "string") return "str";
  if (typeof value === "object") return "dict";
  return typeof value;
}

function validatePath(path: string): void {
  if (path.startsWith("/")) throw new ConfigError(`path must not start with '/': '${path}'`);
  if (path.endsWith("/")) throw new ConfigError(`path must not end with '/': '${path}'`);
  if (path.split("/").includes("..")) throw new ConfigError(`path must not contain '..': '${path}'`);
  if (!PATH_RE.test(path)) throw new ConfigError(`path must match ${PATH_RE.source}: '${path}'`);
}

function validateL3Filename(name: string): void {
  if (!L3_FILENAME_RE.test(name)) {
    throw new ConfigError(`l3 filename must match ${L3_FILENAME_RE.source}: '${name}'`);
  }
}

function validateDescription(text: unknown): void {
  if (typeof text !== "string") {
    throw new ConfigError(`description must be a string, got ${typeName(text)}`);
  }
  if (text === "") throw new ConfigError("description must not be empty");
  if (text.includes("\n") || text.includes("\r")) {
    throw new ConfigError("description must be a single line (no newlines)");
  }
  if (text.length > DESCRIPTION_MAX_LEN) {
    throw new ConfigError(`description must be <= ${DESCRIPTION_MAX_LEN} chars (got ${text.length})`);
  }
}

function validate(parsed: unknown): ParseConfigOutput {
  const errors: ConfigError[] = [];
  let contextDir = "context";

  if (parsed === null || parsed === undefined) {
    return { context_dir: contextDir, categories: defaultCanonicalCategories(contextDir) };
  }
  if (!isPlainObject(parsed)) {
    errors.push(new ConfigError("top-level document must be a mapping"));
    throw new ConfigErrorList(errors);
  }

  for (const key of Object.keys(parsed)) {
    if (!ALLOWED_TOP_LEVEL.has(key)) {
      errors.push(new ConfigError(`unknown top-level key: '${key}'`));
    }
  }

  const rawContextDir = parsed["context_dir"];
  if (rawContextDir !== undefined) {
    if (typeof rawContextDir !== "string" || rawContextDir === "") {
      errors.push(
        new ConfigError(`context_dir must be a non-empty string, got ${pythonRepr(rawContextDir)}`),
      );
    } else {
      try {
        validatePath(rawContextDir);
        contextDir = rawContextDir;
      } catch (e) {
        if (e instanceof ConfigError) errors.push(e);
        else throw e;
      }
    }
  }

  const rawCategories = parsed["categories"];
  let categoriesMap: Record<string, unknown> = {};
  if (rawCategories === undefined || rawCategories === null) {
    categoriesMap = {};
  } else if (!isPlainObject(rawCategories)) {
    errors.push(new ConfigError("categories must be a mapping"));
  } else {
    categoriesMap = rawCategories;
  }

  const resolved: ResolvedCategory[] = [];

  for (const [name, rawBody] of Object.entries(categoriesMap)) {
    if (!CATEGORY_NAME_RE.test(name)) {
      errors.push(
        new ConfigError(`invalid category name: '${name}' (must match ${CATEGORY_NAME_RE.source})`),
      );
      continue;
    }
    if (rawBody !== null && rawBody !== undefined && !isPlainObject(rawBody)) {
      errors.push(new ConfigError(`category '${name}' body must be a mapping`));
      continue;
    }
    const body: Record<string, unknown> =
      rawBody === null || rawBody === undefined ? {} : (rawBody as Record<string, unknown>);

    for (const k of Object.keys(body)) {
      if (!ALLOWED_CATEGORY_FIELDS.has(k)) {
        errors.push(new ConfigError(`category '${name}': unknown field '${k}'`));
      }
    }

    const drop = body["drop"] === true;
    const customFlag = body["custom"] === true;
    const path = body["path"];
    const l3 = body["l3"];
    const description = body["description"];

    if (
      drop &&
      (path !== undefined || customFlag || l3 !== undefined || description !== undefined)
    ) {
      errors.push(
        new ConfigError(`category '${name}': 'drop: true' is mutually exclusive with other fields`),
      );
      continue;
    }

    const isCanonical = RECOGNIZED_CATEGORIES.has(name);
    if (!isCanonical && !customFlag && !drop) {
      const canonicalList = [...RECOGNIZED_CATEGORIES].sort();
      errors.push(
        new ConfigError(
          `category '${name}': non-canonical name requires 'custom: true' ` +
            `(canonical set: ${pythonListRepr(canonicalList)})`,
        ),
      );
      continue;
    }

    let pathStr: string | undefined;
    if (path !== undefined) {
      if (typeof path !== "string") {
        errors.push(new ConfigError(`category '${name}': 'path' must be a string`));
        continue;
      }
      try {
        validatePath(path);
        pathStr = path;
      } catch (e) {
        if (e instanceof ConfigError) {
          errors.push(new ConfigError(`category '${name}': ${e.message}`));
          continue;
        }
        throw e;
      }
    }

    let l3Override: string[] | null = null;
    if (l3 !== undefined) {
      if (!Array.isArray(l3) || !l3.every((x) => typeof x === "string")) {
        errors.push(new ConfigError(`category '${name}': 'l3' must be a list of filename strings`));
        continue;
      }
      const l3Strs = l3 as string[];
      const seen = new Set<string>();
      for (const fname of l3Strs) {
        try {
          validateL3Filename(fname);
        } catch (e) {
          if (e instanceof ConfigError) {
            errors.push(new ConfigError(`category '${name}': ${e.message}`));
          } else {
            throw e;
          }
        }
        if (seen.has(fname)) {
          errors.push(new ConfigError(`category '${name}': duplicate l3 entry '${fname}'`));
        }
        seen.add(fname);
      }
      l3Override = [...l3Strs];
    }

    let descriptionStr: string | null = null;
    if (description !== undefined) {
      try {
        validateDescription(description);
        descriptionStr = description as string;
      } catch (e) {
        if (e instanceof ConfigError) {
          errors.push(new ConfigError(`category '${name}': ${e.message}`));
          continue;
        }
        throw e;
      }
    }

    if (drop) {
      resolved.push({
        name,
        path: null,
        kind: "canonical",
        l3_override: null,
        description: null,
        drop: true,
      });
      continue;
    }

    resolved.push({
      name,
      path: pathStr ?? `${contextDir}/${name}`,
      kind: customFlag ? "custom" : "canonical",
      l3_override: l3Override,
      description: descriptionStr,
      drop: false,
    });
  }

  const declared = new Set(resolved.map((c) => c.name));
  for (const defaultName of CANONICAL_CATEGORIES) {
    if (!declared.has(defaultName)) {
      resolved.push({
        name: defaultName,
        path: `${contextDir}/${defaultName}`,
        kind: "canonical",
        l3_override: null,
        description: null,
        drop: false,
      });
    }
  }

  const active = resolved.filter((c) => !c.drop);
  const seen = new Map<string, string>();
  for (const cat of active) {
    const p = cat.path!;
    if (seen.has(p)) {
      errors.push(new ConfigError(`categories '${seen.get(p)}' and '${cat.name}' share path '${p}'`));
    } else {
      seen.set(p, cat.name);
    }
  }

  const sortedActive = [...active].sort((a, b) =>
    a.path! < b.path! ? -1 : a.path! > b.path! ? 1 : 0,
  );
  for (let i = 0; i < sortedActive.length; i++) {
    const cat = sortedActive[i]!;
    for (let j = i + 1; j < sortedActive.length; j++) {
      const other = sortedActive[j]!;
      if (other.path === cat.path) continue;
      if (other.path!.startsWith(`${cat.path}/`)) {
        errors.push(
          new ConfigError(
            `category '${cat.name}' path '${cat.path}' is a prefix of ` +
              `category '${other.name}' path '${other.path}'`,
          ),
        );
      }
    }
  }

  if (errors.length > 0) throw new ConfigErrorList(errors);

  return { context_dir: contextDir, categories: resolved };
}

function defaultCanonicalCategories(contextDir: string): ResolvedCategory[] {
  return CANONICAL_CATEGORIES.map((name) => ({
    name,
    path: `${contextDir}/${name}`,
    kind: "canonical" as const,
    l3_override: null,
    description: null,
    drop: false,
  }));
}

function emitError(prefix: string, e: ConfigError): void {
  const linePrefix = e.line ? `${prefix}:${e.line}: ` : `${prefix}: `;
  process.stderr.write(`${linePrefix}${e.message}\n`);
}

export function parseConfigFile(path: string): ParseConfigOutput {
  const text = readFileSync(path, "utf-8");
  return validate(parseYaml(text));
}

export function main(argv: string[]): number {
  if (argv.length !== 1) {
    process.stderr.write("usage: parse_config.py <path>\n");
    return 64;
  }

  const pathArg = argv[0]!;
  let stat;
  try {
    stat = statSync(pathArg);
  } catch {
    process.stderr.write(`error: not a file: ${pathArg}\n`);
    return 66;
  }
  if (!stat.isFile()) {
    process.stderr.write(`error: not a file: ${pathArg}\n`);
    return 66;
  }

  const text = readFileSync(pathArg, "utf-8");
  let parsed: unknown;
  try {
    parsed = parseYaml(text);
  } catch (e) {
    if (e instanceof YAMLParseError) {
      const line = e.linePos?.[0]?.line;
      emitError(pathArg, new ConfigError(e.message, line));
      return 65;
    }
    emitError(pathArg, new ConfigError(String((e as Error).message ?? e)));
    return 65;
  }

  let resolved: ParseConfigOutput;
  try {
    resolved = validate(parsed);
  } catch (e) {
    if (e instanceof ConfigErrorList) {
      for (const inner of e.errors) emitError(pathArg, inner);
      return 65;
    }
    if (e instanceof ConfigError) {
      emitError(pathArg, e);
      return 65;
    }
    throw e;
  }

  process.stdout.write(`${JSON.stringify(resolved, null, 2)}\n`);
  return 0;
}

const entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(entry).href) {
  process.exit(main(process.argv.slice(2)));
}
