# Behavior cases

## Should activate

- "Add a `POST /workspaces` handler to our Axum service that returns 201 with the created workspace."
- "Clients get a raw serde error when they send bad JSON to this endpoint. Make it return a proper error and log it."
- "Write middleware that checks the bearer token and puts the user on the request for handlers."
- "Add an endpoint." (in an Axum crate, with no path, method, or payload named; should ask what the endpoint does)

## Should not activate

- "Design the public error type for this Rust SDK crate." (library code with no HTTP layer)
- "Add a `--verbose` flag to this Rust CLI."
- "Add an Express route that lists users." (not Rust)

## Expected behavior

- Defines the route as a `TypedPath` struct registered with `.typed_get()` or `.typed_post()`, or with `.route()` for simple cases, using plural RESTful nouns.
- Keeps granular `thiserror` domain errors separate from a coarse user-facing error that implements `IntoResponse`; the `From` conversion erases details and `inspect_err` logs the real error.
- Reads request bodies with `StrictJson<T>`, not `Json<T>`, and gets database connections, auth, and workspace through custom extractors rather than `Extension<T>`.
- Adds `#[instrument(err, ret, ...)]` to every handler, skipping database connections, auth objects, and request bodies.
- For a public endpoint, adds `#[utoipa::path(...)]` above `#[instrument]` and lists the handler in `routes!`, deriving `ToSchema` on body types and keeping auth extractors out of `params()`.
- Does not invent extractors, helpers, or `AppState` fields the project lacks; when an example names a type the project does not have, it asks or uses the project's equivalent.
