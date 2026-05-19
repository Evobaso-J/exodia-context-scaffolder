#!/usr/bin/env node
// src/schemas.ts
var CANONICAL_CATEGORIES = [
  "architecture",
  "design-patterns",
  "glossary",
  "operations",
  "debugging"
];
var RECOGNIZED_CATEGORIES = new Set(CANONICAL_CATEGORIES);
var PATH_RE = /^[a-z._-][a-z0-9._/-]*$/;
var CATEGORY_NAME_RE = /^[a-z][a-z0-9_-]*$/;
var L3_FILENAME_RE = /^[a-z][a-z0-9_-]*(?:\/[a-z][a-z0-9_-]*)*\.(yaml|jsonl|md)$/;
var DESCRIPTION_MAX_LEN = 200;

export { CANONICAL_CATEGORIES, CATEGORY_NAME_RE, DESCRIPTION_MAX_LEN, L3_FILENAME_RE, PATH_RE, RECOGNIZED_CATEGORIES };
