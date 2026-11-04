#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
//#region src/schemas.ts
/**
* Symlink-tolerant entrypoint check. When the skill dir is a symlink (e.g.
* brain-sync links personal skills into ~/.claude/skills), Node resolves
* import.meta.url to the script's realpath while process.argv[1] keeps the
* symlink path, so a strict href comparison fails and main() silently never
* runs. Canonicalize both sides with realpathSync before comparing.
*/
function isEntrypoint(importMetaUrl, entry) {
	if (!entry) return false;
	try {
		return realpathSync(fileURLToPath(importMetaUrl)) === realpathSync(entry);
	} catch {
		return false;
	}
}
const CANONICAL_CATEGORIES = [
	"architecture",
	"design-patterns",
	"glossary",
	"operations",
	"debugging"
];
const RECOGNIZED_CATEGORIES = new Set(CANONICAL_CATEGORIES);
const PATH_RE = /^[a-z._-][a-z0-9._/-]*$/;
const CATEGORY_NAME_RE = /^[a-z][a-z0-9_-]*$/;
const L3_FILENAME_RE = /^[a-z][a-z0-9_-]*(?:\/[a-z][a-z0-9_-]*)*(?:\.(yaml|md)|\/)$/;
//#endregion
export { RECOGNIZED_CATEGORIES as a, PATH_RE as i, CATEGORY_NAME_RE as n, isEntrypoint as o, L3_FILENAME_RE as r, CANONICAL_CATEGORIES as t };
