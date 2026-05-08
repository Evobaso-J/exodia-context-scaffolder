# Layout fixtures

Hand-written `.exodia.yaml` examples for `/exodia` § Step 0a. Each subdir holds one fixture: the input file (`input.yaml`) and the expected outcome (`expected.txt`). These are documentation-grade fixtures; the validator runs in-Claude during a `/exodia` invocation and cites the rule number on failure.

| Fixture | Outcome | Covers |
|---|---|---|
| `flat/` | pass; flat layout | one-segment leaves, no groups |
| `single-level/` | pass; single-level grouping | one tier of groups over canonical leaves |
| `three-level/` | pass; deep nesting | arbitrary depth (rule 6 has no cap) |
| `list-only/` | pass | `structure:` value is a flat list (no groups) |
| `custom-map/` | pass | custom category as inline single-key map with `purpose` + `ledgers` |
| `collision/` | fail (rule 3) | group name `architecture` collides with leaf `architecture` |
| `invalid-segment/` | fail (rule 2) | leaf `Foo` violates `^[a-z][a-z0-9_-]*$` |

Each `expected.txt` either lists the resolved `category → path` map (pass) or names the failing rule (fail). Add new fixtures here when adding new validation branches.
