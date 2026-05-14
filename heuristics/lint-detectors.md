# Lint/test/typecheck detectors

Scan for commands. Used to decide whether Step 8 should append the inline lint/test/typecheck behavioral rule and to populate its `{{LINT_COMMANDS}}` placeholder.

For content-level consistency checks on the **emitted context tree itself** (e.g. duplicate entity definitions across L2 files, module dossiers leaking into architecture), see `heuristics/content-lints.md`.

| File | Look for |
| ---- | -------- |
| `package.json` | Keys under `scripts` matching `/^(lint|test|type-?check|tsc|eslint|prettier|format)/` |
| `pyproject.toml` | `[tool.poetry.scripts]`, `[tool.pdm.scripts]`, `[project.scripts]`; tools in `dependencies` like `ruff`, `mypy`, `pytest`, `black` |
| `Gemfile` | `rubocop`, `rspec`, `minitest` entries; `Rakefile` task names |
| `Makefile` | Top-level targets `lint`, `test`, `typecheck`, `check` |
| `go.mod` + `Makefile` | `go test`, `go vet`, `staticcheck` targets |
| `Cargo.toml` + Makefile/xtask | `cargo test`, `cargo clippy`, `cargo fmt --check` |

If at least one is detected, Step 8 appends the inline lint/test/typecheck rule to the generated `AGENTS.md` and substitutes the detected commands into the `{{LINT_COMMANDS}}` placeholder as a comma-separated list.
