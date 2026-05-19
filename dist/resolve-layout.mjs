#!/usr/bin/env node
import { readFileSync, statSync, readSync, readdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parse } from 'yaml';

function isDir(p) {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}
function isFile(p) {
  try {
    return statSync(p).isFile();
  } catch {
    return false;
  }
}
function loadCanonicalLedgers(skillDir) {
  const registryPath = join(skillDir, "heuristics", "ledgers.yaml");
  const parsed = parse(readFileSync(registryPath, "utf-8"));
  const out = /* @__PURE__ */ new Map();
  for (const row of Object.values(parsed.ledgers)) {
    const list = out.get(row.filename) ?? [];
    list.push({ host: row.host, schema: row.schema });
    out.set(row.filename, list);
  }
  return out;
}
function categoryTemplateDir(skillDir, name) {
  const candidate = join(skillDir, "templates", name);
  return isDir(candidate) ? candidate : null;
}
function l2TemplatePath(skillDir, name) {
  const src = categoryTemplateDir(skillDir, name);
  if (!src) return null;
  const candidate = join(src, `${name.toUpperCase()}.md.tmpl`);
  return isFile(candidate) ? candidate : null;
}
function l3TemplatePath(skillDir, category, filename) {
  const src = categoryTemplateDir(skillDir, category);
  if (!src) return null;
  const candidate = join(src, `${filename}.tmpl`);
  return isFile(candidate) ? candidate : null;
}
function lookupCanonicalLedger(ledgers, filename, hostCategory) {
  const candidates = ledgers.get(filename);
  if (!candidates || candidates.length === 0) return { schema: null, source: null };
  for (const cand of candidates) {
    if (cand.host === hostCategory) return { schema: cand.schema, source: cand.host };
  }
  const first = candidates[0];
  return { schema: first.schema, source: first.host };
}
function defaultL3Specs(skillDir, ledgers, category) {
  const src = categoryTemplateDir(skillDir, category);
  if (!src) return null;
  const tmpls = [];
  for (const entry2 of readdirSync(src, { withFileTypes: true })) {
    if (entry2.isFile() && entry2.name.endsWith(".tmpl")) tmpls.push(entry2.name);
  }
  tmpls.sort();
  const specs = [];
  for (const tmpl of tmpls) {
    const base = tmpl.slice(0, -".tmpl".length);
    if (base.endsWith(".md")) continue;
    if (!base.endsWith(".jsonl") && !base.endsWith(".yaml")) continue;
    const { schema } = lookupCanonicalLedger(ledgers, base, category);
    specs.push({
      filename: base,
      schema_name: schema,
      schema_template_path: join(src, tmpl)
    });
  }
  return specs;
}
function resolveLayout(parsed, skillDir) {
  const ledgers = loadCanonicalLedgers(skillDir);
  const out = [];
  for (const cat of parsed.categories) {
    if (cat.drop) continue;
    const name = cat.name;
    const kind = cat.kind;
    const l3Override = cat.l3_override;
    const description = cat.description ?? null;
    const l2Path = kind === "canonical" ? l2TemplatePath(skillDir, name) : null;
    let l3Specs;
    if (l3Override !== null) {
      l3Specs = [];
      for (const fname of l3Override) {
        if (fname.endsWith(".md")) {
          l3Specs.push({ filename: fname, schema_name: null, schema_template_path: null });
          continue;
        }
        const { schema, source } = lookupCanonicalLedger(ledgers, fname, name);
        let tmplPath = null;
        if (source !== null) {
          const p = l3TemplatePath(skillDir, source, fname);
          tmplPath = p ?? null;
        }
        l3Specs.push({
          filename: fname,
          schema_name: schema,
          schema_template_path: tmplPath
        });
      }
    } else if (kind === "canonical") {
      l3Specs = defaultL3Specs(skillDir, ledgers, name);
    } else {
      l3Specs = null;
    }
    out.push({
      name,
      path: cat.path,
      kind,
      description,
      l2_template_path: l2Path ?? null,
      l3_specs: l3Specs
    });
  }
  return out;
}
function parseArgs(argv) {
  let skillDir = null;
  let config = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--skill-dir") {
      const v = argv[++i];
      if (!v) return { error: "argument --skill-dir: expected one argument" };
      skillDir = v;
    } else if (a.startsWith("--skill-dir=")) {
      skillDir = a.slice("--skill-dir=".length);
    } else if (a === "--config") {
      const v = argv[++i];
      if (!v) return { error: "argument --config: expected one argument" };
      config = v;
    } else if (a.startsWith("--config=")) {
      config = a.slice("--config=".length);
    } else {
      return { error: `unrecognized argument: ${a}` };
    }
  }
  if (!skillDir) return { error: "the following arguments are required: --skill-dir" };
  return { skillDir, config };
}
function readStdinSync() {
  const chunks = [];
  const buf = Buffer.alloc(65536);
  for (; ; ) {
    let bytes = 0;
    try {
      bytes = readSync(0, buf, 0, buf.length, null);
    } catch {
      break;
    }
    if (bytes <= 0) break;
    chunks.push(Buffer.from(buf.subarray(0, bytes)));
  }
  return Buffer.concat(chunks).toString("utf-8");
}
function main(argv) {
  const parsed = parseArgs(argv);
  if ("error" in parsed) {
    process.stderr.write(`error: ${parsed.error}
`);
    return 64;
  }
  const skillDir = resolve(parsed.skillDir);
  if (!isDir(skillDir)) {
    process.stderr.write(`error: skill dir not found: ${skillDir}
`);
    return 66;
  }
  let text;
  if (parsed.config) {
    text = readFileSync(parsed.config, "utf-8");
  } else {
    text = readStdinSync();
  }
  const parsedJson = JSON.parse(text);
  const resolved = resolveLayout(parsedJson, skillDir);
  process.stdout.write(`${JSON.stringify(resolved, null, 2)}
`);
  return 0;
}
var entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(entry).href) {
  process.exit(main(process.argv.slice(2)));
}

export { main, resolveLayout };
