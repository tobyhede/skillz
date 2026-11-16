# Provenance

This skill is adapted from the Axum service conventions skill in the CipherStash monorepo, with company-specific names replaced by neutral ones.

- Upstream: `cipherstash/cipherstash-suite`, path `.claude/skills/rust-axum/` (private repository)
- Commit: `176e507515e3438e1502c8f996d22b41067c0d2d`
- Author: Dan Draper (CipherStash)
- License: none declared upstream (the source repository is private)
- Imported: 2026-11-16

## Local changes

Upstream ships only `SKILL.md`. This copy started from it and has since been revised against Axum 0.8.8, axum-extra 0.10, tower-http 0.6, tracing 0.1, utoipa 5.4, and utoipa-axum 0.2, following a review of the guidance against those releases. It is no longer a near-copy, so a future update is a merge by hand rather than a clean diff.

- Layout: the OpenAPI section lives in `references/openapi.md`, since the skillz contract caps `SKILL.md` at 500 lines.
- Company-specific identifiers (crate paths, config type, a permission type, the workspace header, the JWT scheme name, the API title, an endpoint host, the docs env var) are replaced with neutral ones.
- Request bodies: the `StrictJson` helper that buffered the body into memory, logged it, and unwrapped read errors is removed. The skill now uses `Json`/`Form` or a wrapper that delegates once, logs only a rejection classification, and keeps protocol rejections with `WithRejection`.
- Tracing: request spans record the `MatchedPath` template with a fixed fallback instead of the raw path. Handler examples use `skip_all` with named fields. The `ret`-on-redirect example is removed, with rules on `ret`, `err`, and `?`/`%`/URL formatting.
- Errors: domain errors are mapped at the boundary preserving status, headers, content type, and machine-readable codes, replacing the rule that every conversion erases details and that domain errors never implement `IntoResponse`.
- Layers: corrected to say `.layer()` and `.route_layer()` wrap only routes registered before the call, with the `route_layer` 404 behavior and the `.layer` versus `ServiceBuilder` ordering. The middleware example takes `mut req`.
- New sections: a pre-change checklist; state, extensions, and authorization (including that `security(...)` documents rather than enforces); async and Tokio; and testing through the mounted router.
- `references/openapi.md`: `ToParam` (not a utoipa derive) is replaced with `IntoParams`, inline `params(...)`, and `ToSchema`. Blanket camelCase is replaced with "keep existing wire names". Adds `TypedPath` alongside `routes!`, compatibility aliases, spec tests, and registers the `jwt` security scheme the examples reference.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `PROVENANCE.md`: this file.

The examples use domain names such as workspaces, access keys, and OAuth device flow, and helper types such as `DualPool` and `JsonResponse`. They illustrate the patterns; apply them with the project's own names.

To update, read the upstream diff since the commit above, carry over any guidance that still holds, and bump the commit here.
