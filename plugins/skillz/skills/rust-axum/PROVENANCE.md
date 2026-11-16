# Provenance

This skill is adapted from the Axum service conventions skill in the CipherStash monorepo, with company-specific names replaced by neutral ones.

- Upstream: `cipherstash/cipherstash-suite`, path `.claude/skills/rust-axum/` (private repository)
- Commit: `176e507515e3438e1502c8f996d22b41067c0d2d`
- Author: Dan Draper (CipherStash)
- License: none declared upstream (the source repository is private)
- Imported: 2026-11-16

## Local changes

Upstream ships only `SKILL.md`. Its guidance is unchanged; the edits below are layout, renamed identifiers, and two example fixes.

- `SKILL.md`: the OpenAPI section moved to `references/openapi.md` (the skillz contract caps `SKILL.md` at 500 lines), leaving a short summary that links to it. Its `###` headings became `##` and a table of contents was added.
- Company-specific identifiers in examples are renamed: crate paths in comments (`domain/`, `web/`), the config type (`Config`), a permission type, the workspace header (`x-workspace-id`), the JWT security scheme name (`jwt`), the API title, an example endpoint host (`api.example.com`), and the OpenAPI docs env var. The intro to the extractor list no longer says "in this codebase".
- `SKILL.md`: the standard `#[instrument]` example now skips `request`, matching its own rule to always skip request bodies.
- `references/openapi.md`: the moved OpenAPI section, with the renames above. `build_api_doc` also registers the `jwt` security scheme that the handler examples reference.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `PROVENANCE.md`: this file.

The examples use domain names such as workspaces, access keys, and OAuth device flow, and helper types such as `DualPool`, `StrictJson`, and `JsonResponse`. They illustrate the patterns; apply them with the project's own names.

To update, diff `.claude/skills/rust-axum/` at a newer upstream commit against this directory and bump the commit here.
