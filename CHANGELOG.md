# Changelog

## [2.2.0](https://github.com/Evobaso-J/exodia-context-scaffolder/compare/v2.1.0...v2.2.0) (2026-05-17)


### Features

* allow nested-dir paths in `categories.<name>.l3:` config ([#74](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/74)) ([4fed8b3](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/4fed8b3abe8d2b1774530cd5c96d59a47252f9d5))

## [2.1.0](https://github.com/Evobaso-J/exodia-context-scaffolder/compare/v2.0.0...v2.1.0) (2026-05-15)


### Features

* allow .md filenames in `categories.<name>.l3:` config ([#72](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/72)) ([916a616](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/916a6169a7b189112cb9586a2d706741de5c2290))

## [2.0.0](https://github.com/Evobaso-J/exodia-context-scaffolder/compare/v1.1.0...v2.0.0) (2026-05-15)


### ⚠ BREAKING CHANGES

* **skill:** design-patterns L2 template no longer ships fixed section headings (Components, Reusable Utilities, API & External Services, Authentication, Observability / Telemetry, Testing, Accessibility & i18n). Existing scaffolds keep their old markers through the legacy section-id diff path; fresh scaffolds use the new H2-slug path.
* **skill:** emitted AGENTS.md no longer contains the lint/test/typecheck bullet, the File Format Strategy block, or the "When adding a new L3 file" paragraph. Existing scaffolded repos keep their current AGENTS.md until re-emitted.
* **skill:** existing exodia.config.yaml files declaring mobile / infra / data / workspace categories will now fail validation unless custom: true is added. No grandfathering. Cross-repo consistency for non-core categories becomes a user responsibility via shared exodia.config.yaml snippets.
* **skill:** model-driven category proposal, drop trigger table ([#59](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/59))
* **skill:** gotchas.jsonl is no longer scaffolded. Repos that relied on the canonical debugging/gotchas.jsonl path will need to keep the inherited file in place, or migrate entries to playbooks.jsonl.

### Features

* **skill:** config-driven layout via opt-in exodia.config.yaml ([#39](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/39)) ([335bab6](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/335bab68b59c46ce07b729765076c82251ebd055))
* **skill:** drop gotchas.jsonl from debugging ([#58](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/58)) ([bb7be23](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/bb7be23fe4b3a5bd560f32bdb72dad21f617d5ae))
* **skill:** optional `description` field in `exodia.config.yaml` ([#66](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/66)) ([c5a83ef](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/c5a83ef0e7cb02aa1c9af1a1136fdbc2f016ee8f))
* **skill:** progressive disclosure for design-patterns module ([#65](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/65)) ([023c92a](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/023c92ac76918f75fbffc9fe67d0b2692e0aecc4))


### Code Refactoring

* **skill:** drop curation of optional categories; core 5 only ([#60](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/60)) ([92eed97](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/92eed97b463378ec5acda3b582f075024be7039c))
* **skill:** drop lint-policy rule and File Format Strategy from emitted AGENTS.md ([#64](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/64)) ([73620e7](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/73620e774bfd2fa64e734cc1188ae24db3097a42))
* **skill:** model-driven category proposal, drop trigger table ([#59](https://github.com/Evobaso-J/exodia-context-scaffolder/issues/59)) ([2222ad6](https://github.com/Evobaso-J/exodia-context-scaffolder/commit/2222ad6d5b28b5008bf87805c5a0a6e39bb51ad2))

## [1.1.0](https://github.com/Evobaso-J/exodia-scaffolder/compare/v1.0.0...v1.1.0) (2026-05-02)


### Features

* **skill:** seed all L3 files in Step 9, not just five ([#36](https://github.com/Evobaso-J/exodia-scaffolder/issues/36)) ([17a844a](https://github.com/Evobaso-J/exodia-scaffolder/commit/17a844a2e039a250d442a862e5f1aeebf205d45f))
