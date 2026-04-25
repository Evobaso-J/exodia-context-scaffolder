## [0.1.0] - 2026-04-25

### 🚀 Features

- Initial /exodia skill scaffolder

### 🐛 Bug Fixes

- Low-risk review findings (#4)
- Close TOCTOU in symlink probe (#5)
- Reconcile rename affordance with init_structure validation (#10)
- Validate settings.json shape before merging Stop hook (#6)
- Drop over-scoped "stop-hook failures are blockers" rule (#9)

### 🚜 Refactor

- Merge-mode: ask consent up front, drop .bak files (#11)
- De-opinionate scaffolder: drop WeRoad flavor, canon enforcement, hardcoded runtimes (#15)
- Drop pointer-files feature (#16)
- Ship as skill, drop dead plugin shell (#21)
- Drop optional Stop hook, lean on prose self-update rules (#26)
- Flatten skill layout for one-line install (#27)

### 📚 Documentation

- Add hero image, flavor tagline, and credits to README (#1)
- Remove donor-repo reference from SKILL.md tone section (#2)
- *(skill)* Forbid duplicating repo data in L2 drafts (#3)
- *(skill)* Align with digital-brain-skill source material (#13)
- Rewrite README to match current skill surface (#17)
- Remove em-dashes from README (#18)
- Reorder Install above the fold + table-ize self-update rules (#19)
- Clarify what the optional Stop hook actually does (#20)
- Tighten Credits: drop overstated claim, name the upstream pattern (#22)
- Label Router as L1 in How it works (#23)
- *(skill)* Use $CONTEXT_DIR in runtime path refs (#25)
- Trim README, defer protocol detail to SKILL.md (#28)

### ⚙️ Miscellaneous Tasks

- Drop redundant root AGENTS.md (#24)
