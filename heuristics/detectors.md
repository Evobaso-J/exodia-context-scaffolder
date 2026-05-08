# Category-tweak detectors

How `/exodia` decides which optional categories to propose, beyond the fixed 5 (architecture, patterns, domain, operations, debugging).

The Explore subagent reports which triggers fire. Apply this table verbatim.

## Optional adds

| Trigger (any of) | Add category | Template |
| ---------------- | ------------ | -------- |
| `package.json` deps include one of: `react-native`, `expo`, `@react-native-*` • Top-level `ios/` + `android/` dirs • Presence of `*.swift`, `*.kt`, `*.xcodeproj` • `pubspec.yaml` + `lib/` with Dart files | `mobile/` | `templates/mobile/MOBILE.md.tmpl` |
| `pnpm-workspace.yaml` • `turbo.json` • `nx.json` • `lerna.json` • `apps/` + `packages/` dirs with separate `package.json` in each | `workspace/` | `templates/workspace/WORKSPACE.md.tmpl` |
| Deps include one of: `torch`, `tensorflow`, `jax`, `scikit-learn`, `pandas`, `numpy` with training code • Presence of `notebooks/`, `models/`, `data/` directories • `.ipynb` files in tracked paths • `dvc.yaml` | `data/` | `templates/data/DATA.md.tmpl` |
| `*.tf` files • `terraform/` dir • `helm/` dir with `Chart.yaml` • `k8s/` or `kustomize/` dirs • `cdk.json` • `pulumi.yaml` • `cloudformation/` | `infra/` | `templates/infra/INFRA.md.tmpl` |

## Propose, don't impose

After computing adds, present the full proposed set to the user with `AskUserQuestion`. The user may:

- Accept as proposed
- Drop optional categories they don't want
- Add a custom category not in the table (skill must then ask for a short purpose statement and any L3 ledgers needed, picking formats per `heuristics/format-strategy.md`; `init_structure.sh` scaffolds an empty L2 stub for categories without a template dir, and Step 6 drafts the L3 stubs alongside)

The canonical five are a strong default, not an enforced minimum. Users may drop any that do not apply to the target (e.g. a pure library often has no `operations/`; a data pipeline may not need `patterns/`). `init_structure.sh` validates that each requested name matches `^[a-z][a-z0-9_-]*$`, so the name may be any path-safe lowercase segment.

## Lint/test/typecheck detection

Scan for commands. Used to decide whether to insert the `lint-check.md` rule and to populate its placeholder.

| File | Look for |
| ---- | -------- |
| `package.json` | Keys under `scripts` matching `/^(lint|test|type-?check|tsc|eslint|prettier|format)/` |
| `pyproject.toml` | `[tool.poetry.scripts]`, `[tool.pdm.scripts]`, `[project.scripts]`; tools in `dependencies` like `ruff`, `mypy`, `pytest`, `black` |
| `Gemfile` | `rubocop`, `rspec`, `minitest` entries; `Rakefile` task names |
| `Makefile` | Top-level targets `lint`, `test`, `typecheck`, `check` |
| `go.mod` + `Makefile` | `go test`, `go vet`, `staticcheck` targets |
| `Cargo.toml` + Makefile/xtask | `cargo test`, `cargo clippy`, `cargo fmt --check` |

If at least one is detected, insert `rules/conditional/lint-check.md` into the generated `AGENTS.md` and substitute the detected commands into the `{{LINT_COMMANDS}}` placeholder as a comma-separated list.
