# Behavior cases

## Should activate

- "Add a documented, protected `POST /workspaces` endpoint to our Axum service that returns 201 with the created workspace."
- "Add an OAuth device-flow step that redirects the browser to the activation page with the user code."
- "Clients sending malformed JSON to the credential exchange get a confusing error. Diagnose it and make the response consistent."
- "Write middleware that checks the bearer token and puts the principal on the request for handlers."
- "Add an endpoint." (in an Axum crate, with no path, method, payload, or access rule named; should ask what the endpoint does and who may call it)

## Should not activate

- "Design the public error type for this Rust SDK crate." (library code with no HTTP layer)
- "Add a `--verbose` flag to this Rust CLI."
- "Add an Express route that lists users." (not Rust)

## Expected behavior

- Finds where the route is mounted before adding it, and places it inside or outside the auth layer deliberately; knows `.layer()` and `.route_layer()` cover only routes registered before the call, and that `.layer(a).layer(b)` runs `b` first.
- Extracts bodies with `Json<T>`, `Form<T>`, or a wrapper that delegates to them once; never buffers or logs the raw body or a deserializer error's full text; keeps a protocol rejection contract such as `WithRejection` on OAuth forms.
- Maps domain errors at the boundary while preserving status, headers, content type, and machine-readable error codes; does not erase every variant into one generic error by reflex.
- Records the matched route template (`MatchedPath`, fixed fallback for unmatched) rather than `uri().path()` in request spans; uses `skip_all` with named safe fields on handlers, and never puts `ret` on a redirect or other value that can carry a code or token.
- Checks permission, tenant scope, and credential kind for the operation, and treats `security(...)` in the OpenAPI annotation as documentation, not enforcement.
- For a documented endpoint, uses `#[utoipa::path]` plus `routes!`, `IntoParams` or inline `params(...)` for parameters, `ToSchema` for body and parameter value types, and keeps existing wire names (no blanket camelCase on OAuth fields); never derives `ToParam`.
- Tests through the mounted router: 401, 403, cross-tenant, public route, and unknown-path 404 cases; rejection statuses; and a synthetic marker proving no body or path value reaches captured logs.
- Does not invent extractors, helpers, or `AppState` fields the project lacks; when an example names a type the project does not have, it asks or uses the project's equivalent.
