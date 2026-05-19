#!/usr/bin/env node
import { mkdirSync, statSync, existsSync, writeFileSync, readdirSync, copyFileSync } from 'node:fs';
import { resolve, dirname, join, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

var CONTEXT_DIR_RE = /^[a-z._-][a-z0-9._-]*$/;
var CATEGORY_RE = /^[a-z][a-z0-9_-]*$/;
var SCRIPT_FILE = fileURLToPath(import.meta.url);
var SKILL_DIR = resolve(dirname(SCRIPT_FILE), "..");
var TEMPLATES = join(SKILL_DIR, "templates");
function isDir(p) {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}
function templateDirFor(cat) {
  const p = join(TEMPLATES, cat);
  return isDir(p) ? p : null;
}
function l2StubBody(upper) {
  return `# ${upper}

<!-- exodia:section:intro -->
TODO: describe what this module covers.

<!-- exodia:section:purpose -->
## Purpose

TODO

<!-- exodia:section:key-files -->
## Key Files

TODO

<!-- exodia:section:l3 -->
## L3 Data

TODO
`;
}
function copyCategoryTo(cat, absDest) {
  const srcDir = templateDirFor(cat);
  mkdirSync(absDest, { recursive: true });
  if (!srcDir) {
    const upper = cat.toUpperCase();
    const stub = join(absDest, `${upper}.md`);
    if (existsSync(stub)) {
      process.stdout.write(`skip (exists): ${stub}
`);
    } else {
      writeFileSync(stub, l2StubBody(upper), "utf-8");
      process.stdout.write(`wrote: ${stub}
`);
    }
    return;
  }
  const topLevel = readdirSync(srcDir, { withFileTypes: true });
  const tmpls = topLevel.filter((e) => e.isFile() && e.name.endsWith(".tmpl")).map((e) => e.name).sort();
  for (const tmpl of tmpls) {
    const base = tmpl.slice(0, -".tmpl".length);
    const dest = join(absDest, base);
    if (existsSync(dest)) {
      process.stdout.write(`skip (exists): ${dest}
`);
      continue;
    }
    copyFileSync(join(srcDir, tmpl), dest);
    process.stdout.write(`wrote: ${dest}
`);
  }
  const subdirs = topLevel.filter((e) => e.isDirectory()).map((e) => e.name).sort();
  for (const sub of subdirs) {
    const subSrc = join(srcDir, sub);
    const destSub = join(absDest, sub);
    mkdirSync(destSub, { recursive: true });
    const inner = readdirSync(subSrc, { withFileTypes: true }).filter((e) => e.isFile() && !e.name.endsWith(".tmpl")).map((e) => e.name).sort();
    for (const fname of inner) {
      const fdest = join(destSub, basename(fname));
      if (existsSync(fdest)) {
        process.stdout.write(`skip (exists): ${fdest}
`);
        continue;
      }
      copyFileSync(join(subSrc, fname), fdest);
      process.stdout.write(`wrote: ${fdest}
`);
    }
  }
}
function usage() {
  process.stderr.write("usage: init_structure.sh <target-dir> <context-dir> <category> [...]\n");
  process.stderr.write("       init_structure.sh <target-dir> --pairs <name>=<path> [...]\n");
}
function main(argv) {
  if (argv.length < 2) {
    usage();
    return 64;
  }
  const target = argv[0];
  const rest = argv.slice(1);
  if (!isDir(target)) {
    process.stderr.write(`error: target dir does not exist: ${target}
`);
    return 66;
  }
  if (rest[0] === "--pairs") {
    const pairs = rest.slice(1);
    if (pairs.length < 1) {
      process.stderr.write("error: --pairs requires at least one <name>=<path> pair\n");
      return 64;
    }
    for (const pair of pairs) {
      const eqIdx = pair.indexOf("=");
      if (eqIdx === -1) {
        process.stderr.write(`error: malformed pair (expected name=path): '${pair}'
`);
        return 65;
      }
      const name = pair.slice(0, eqIdx);
      const path = pair.slice(eqIdx + 1);
      if (!name || !path) {
        process.stderr.write(`error: malformed pair (empty name or path): '${pair}'
`);
        return 65;
      }
      copyCategoryTo(name, join(target, path));
    }
    const noun = pairs.length === 1 ? "category" : "categories";
    process.stdout.write(`done. ${pairs.length} ${noun} materialized at config-declared paths
`);
    return 0;
  }
  const contextDir = rest[0];
  const categories = rest.slice(1);
  if (categories.length < 1) {
    process.stderr.write("usage: init_structure.sh <target-dir> <context-dir> <category> [category ...]\n");
    return 64;
  }
  if (!contextDir || contextDir === "." || contextDir === "..") {
    process.stderr.write(`error: invalid context dir name: '${contextDir}'
`);
    return 65;
  }
  if (!CONTEXT_DIR_RE.test(contextDir)) {
    process.stderr.write(
      `error: invalid context dir name: '${contextDir}' (must match ${CONTEXT_DIR_RE.source})
`
    );
    return 65;
  }
  for (const c of categories) {
    if (!CATEGORY_RE.test(c)) {
      process.stderr.write(`error: invalid category name: '${c}' (must match ${CATEGORY_RE.source})
`);
      return 65;
    }
  }
  mkdirSync(join(target, contextDir), { recursive: true });
  for (const cat of categories) {
    copyCategoryTo(cat, join(target, contextDir, cat));
  }
  process.stdout.write(`done. ${contextDir}/ initialized at ${join(target, contextDir)}
`);
  return 0;
}
var entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(entry).href) {
  process.exit(main(process.argv.slice(2)));
}

export { main };
