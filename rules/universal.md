1. **Route first.** Use the Context Router table above before loading any data file. Do not guess; the router exists to avoid guessing.
2. **Load lazily.** Never load all L3 files at once. Max 2 hops: router → L2 narrative → (optional) L3 data. If the task is answerable from L2 alone, stop there.
3. **Append only.** `.jsonl` data files are append-only. When an entry becomes obsolete, mark it `archived`; do not delete.
4. **Rationale required.** ADRs and decisions must include *why*. An entry without a reason will rot.
5. **Read before write.** Before appending to a data file, scan it for a duplicate or near-duplicate. Update or supersede rather than create a duplicate.
6. **Existing patterns win.** Read `{{CONTEXT_DIR}}/patterns/PATTERNS.md` before introducing a new convention. If an existing pattern covers the case, use it.
7. **IDs are timestamps.** All L3 entries use the format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` where `{type}` is the target file's `_schema` value (first line of the `.jsonl`). This makes IDs sortable and collision-free.
8. **Context update as final task.** When planning work with a todo list, always add a final step: "Evaluate context update." At that step, walk the §Self-Update Rules table below and decide if any entry should be captured. If nothing qualifies, skip. Do not create entries just to fill the step.
