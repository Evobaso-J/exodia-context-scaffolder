import { defineConfig } from "tsup";

export default defineConfig({
  entry: {
    "parse-config": "src/parse-config.ts",
    "resolve-layout": "src/resolve-layout.ts",
    "init-structure": "src/init-structure.ts",
  },
  format: ["esm"],
  outDir: "dist",
  outExtension: () => ({ js: ".mjs" }),
  target: "node20",
  platform: "node",
  bundle: true,
  splitting: false,
  sourcemap: false,
  clean: true,
  minify: false,
  treeshake: true,
  shims: false,
  dts: false,
  banner: {
    js: "#!/usr/bin/env node",
  },
});
