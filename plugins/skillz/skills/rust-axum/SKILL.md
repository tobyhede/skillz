---
name: rust-axum
description: Apply when building or modifying Axum HTTP services, handlers, middleware, or extractors. TRIGGER when creating or editing Axum route handlers, defining error types that implement IntoResponse, writing middleware functions, building custom extractors (FromRequest/FromRequestParts), configuring Router, or structuring AppState. DO NOT TRIGGER when writing library/SDK code with no HTTP layer, pure domain logic, CLI tools, or non-Rust files.
user-invocable: false
---

# Axum Service Development

Conventions for changing an Axum HTTP service without changing its wire behavior, widening its
access boundary, or leaking request data into logs. The examples target Axum 0.8, axum-extra
0.10, tower-http 0.6, and tracing 0.1. Check signatures against the versions in the project's
`Cargo.lock`, and treat a dependency upgrade as a separate change.

## Before you change an endpoint

1. Find where the route is actually mounted: which router, what is registered before and after
   it, and which layers wrap it. See [Middleware and layer placement](#middleware-and-layer-placement).
2. Read the existing request and response contract: content type, rejection statuses and
   bodies, error shape, and any compatibility aliases. Preserve it unless the task is to change it.
3. Identify what the endpoint authorizes beyond "a caller is authenticated". See
   [State, extensions, and authorization](#state-extensions-and-authorization).
4. Find the existing tests for the route, and plan a test that drives the mounted router. See
   [Testing](#testing).

## RESTful routes and TypedPath

Use `axum_extra::routing::TypedPath` for compile-time checked routes and links. Define routes as
unit or field structs with `#[typed_path("/path")]`.

```rust
use axum_extra::routing::TypedPath;
use serde::Deserialize;

#[derive(Debug, TypedPath, Deserialize)]
#[typed_path("/oauth/device/token")]
pub struct DeviceTokenPath;

#[derive(Debug, TypedPath, Deserialize)]
#[typed_path("/oauth/device/confirm/{user_code}")]
pub struct ConfirmPath {
    user_code: UserCode,
}
```

Build links from the typed path rather than from strings:

```rust
let dest = ActivatePath.with_query_params(user_code_param).to_uri().to_string();
Redirect::to(&dest)

let callback_url = state.url_for(PkceCallbackPath)?; // base URL + typed path
```

Register typed routes with `.typed_get()` / `.typed_post()`, and simple ones with `.route()`:

```rust
let router = Router::new()
    .typed_post(oauth::device::token)
    .typed_get(oauth::device::activate)
    .route("/health", get(async || StatusCode::OK))
    .route("/workspaces", get(workspace::list).post(workspace::create));
```

Rules:
- RESTful naming: plural nouns (`/workspaces`, `/memberships`), standard HTTP methods
- A TypedPath handler's first parameter is the path struct (e.g. `_: DeviceTokenPath`)
- Build redirects with `.to_uri()` and absolute URLs with a helper such as `state.url_for(path)`;
  never hardcode route strings
- A path parameter's value appears in the request URI. Anything that logs the URI logs it; see
  [Tracing](#tracing)
- Documented handlers may be mounted with utoipa's `routes!` while still using `TypedPath` for
  extraction; see [references/openapi.md](references/openapi.md)

## Errors and responses

Keep detailed domain errors where they help diagnosis, and decide at the HTTP boundary what the
client sees. The boundary mapping must preserve the contract clients rely on: status code,
headers, content type, and any machine-readable fields such as an OAuth `error` code.

### Domain errors

Fine-grained `thiserror` enums with `#[from]` for upstream errors:

```rust
#[derive(Debug, thiserror::Error)]
pub enum DeviceAuthRequestError {
    #[error("failed to generate user code: {0}")]
    UserCodeGenerationFailed(#[from] RandomError),

    #[error("missing config: {0}")]
    ConfigMissing(String),

    #[error("storage error: {0}")]
    StorageError(#[from] DeviceCodeError),
}
```

### Mapping at the boundary

Map each domain variant to what the client needs to know. Infrastructure faults usually collapse
to a generic 500 with the detail logged; a client-actionable failure keeps a status and code the
client can act on. Do not erase every variant into one response by reflex, and do not leak
internal messages, paths, or stack traces.

```rust
#[derive(Debug, Clone, Serialize, thiserror::Error)]
#[serde(tag = "error", rename_all = "snake_case")]
pub enum OAuthError {
    #[error("invalid request")]
    InvalidRequest,
    #[error("authorization pending")]
    AuthorizationPending,
    #[error("server error")]
    ServerError,
}

impl From<DeviceAuthRequestError> for OAuthError {
    fn from(err: DeviceAuthRequestError) -> Self {
        match err {
            // Every variant here is an internal fault, so all map to server_error. A
            // client-caused variant (bad code, expired code) would map to its own OAuth code.
            DeviceAuthRequestError::ConfigMissing(_)
            | DeviceAuthRequestError::UserCodeGenerationFailed(_)
            | DeviceAuthRequestError::StorageError(_) => {
                tracing::error!(error = %err, "device authorization failed");
                OAuthError::ServerError
            }
        }
    }
}

impl IntoResponse for OAuthError {
    fn into_response(self) -> Response {
        let status = match self {
            Self::InvalidRequest | Self::AuthorizationPending => StatusCode::BAD_REQUEST,
            Self::ServerError => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (status, Json(self)).into_response()
    }
}
```

In handlers, log the real error and return the mapped one. Log the error's `Display` only when
you know it cannot contain credentials or request values:

```rust
let claims = verify_service_token(token, &auth.jwk_manager())
    .await
    .inspect_err(|e| tracing::warn!(error = %e, "service token rejected"))
    .map_err(|_| AuthError::Unauthorized)?;
```

Rules:
- A handler returning `Result<T, E>` where `E: IntoResponse` always produces an HTTP response;
  the mapping in `IntoResponse` is the contract, so review it before changing it
- A domain error may implement `IntoResponse` when its mapping is the boundary contract; when the
  type lives in another crate, wrap it in a local newtype (e.g. `ErrorResponse<T>`)
- Keep distinctions clients or operators need, such as a rejected credential (401) versus a
  verification backend being unavailable (503)
- JSON errors: `(status, Json(body)).into_response()`; plain text: `(status, msg).into_response()`
- Tower middleware that returns a service error (timeouts, load shedding) needs
  `HandleErrorLayer` or an equivalent outer handler to turn it into a response

## Extracting requests

Extractors run left to right. `FromRequestParts` extractors (state, headers, path, identity) come
first; exactly one body-consuming `FromRequest` extractor comes last.

### Request bodies

Use Axum's `Json<T>` or `Form<T>`, or the endpoint's existing wrapper, so a bad request gets the
standard rejection: 415 for a wrong content type, 400 for malformed syntax, 422 for valid JSON
with the wrong shape, and 413 over the body limit.

Never buffer the body to log it, and never log a deserializer error's full text: both can contain
credentials or other submitted values, and buffering before the extractor reads the body defeats
the streaming body limit. Log a classification of the rejection instead.

```rust
// GOOD — native extraction, safe diagnostics
pub async fn create(
    State(state): State<AppState>,
    payload: Result<Json<CreateRequest>, JsonRejection>,
) -> Result<JsonResponse<CreateResponse>, ApiError> {
    // ApiError: From<JsonRejection> keeps the standard status and message
    let Json(request) = payload.inspect_err(|rejection| {
        tracing::info!(status = %rejection.status(), "rejected JSON body");
    })?;
    // ...
}

// GOOD — a project wrapper delegates to Json exactly once
impl<T, S> FromRequest<S> for AppJson<T>
where
    T: DeserializeOwned,
    S: Send + Sync,
{
    type Rejection = JsonRejection;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        Json::<T>::from_request(req, state).await.map(|Json(v)| AppJson(v))
    }
}

// BAD — reads the whole body before the limit applies, logs it, and panics on a read error
let bytes = buffer_and_print("request", body).await.unwrap();
```

When a protocol defines its own rejection body (OAuth expects a 400 with an `error` field for a
malformed form), keep it with `axum_extra::extract::WithRejection`:

```rust
pub async fn token(
    _: DeviceTokenPath,
    State(state): State<AppState>,
    WithRejection(Form(request), _): WithRejection<Form<DeviceTokenRequest>, OAuthFormRejection>,
) -> Result<JsonResponse<DeviceTokenResponse>, OAuthError> { ... }
```

Replacing such an extractor with plain `Form<T>` changes the wire contract.

### Custom extractors

Prefer a named extractor over `Extension<T>` in handler signatures: it states the dependency,
documents its rejection, and is reusable.

```rust
pub struct ReadDb(pub PgConn);

impl FromRequestParts<AppState> for ReadDb {
    type Rejection = ApiError;

    async fn from_request_parts(_parts: &mut Parts, state: &AppState) -> Result<Self, Self::Rejection> {
        let pool = DualPool::from_ref(state);
        PgConn::checkout(pool.for_read()).await.map(ReadDb).map_err(ApiError::pool_unavailable)
    }
}
```

An extractor that reads an extension written by middleware is still only as good as the
middleware wiring: it must reject cleanly when the extension is missing, and the route must be
inside the layer that writes it.

## State, extensions, and authorization

| What | Where it belongs |
|---|---|
| Shared dependencies (pools, config, auth services) | `State<AppState>`, with `FromRef` for the narrower pieces extractors need. Keep it cheap to clone. |
| Identity computed for this request | Authentication middleware writes a request extension; a downstream extractor reads it and rejects if absent. |
| Authorization of this operation | Explicit checks in the extractor, handler, or domain call: permission, tenant or resource scope, and credential kind where it matters. |
| Request body | One body-consuming extractor, last in the signature. |

```rust
#[derive(Clone)]
pub struct AppState {
    pub base_url: Url,
    pub auth: Authorization,
    pub config: Arc<Config>,
    pub pool: DualPool,
    pub activate_rate_limiter: RateLimiter,
}

impl FromRef<AppState> for DualPool {
    fn from_ref(state: &AppState) -> Self {
        state.pool.clone()
    }
}
```

Rules:
- `AppState` must be `Clone`; wrap large or non-`Clone` fields in `Arc<T>`
- A principal in the request proves only that middleware found a valid identity. Check the
  permission, the tenant that owns the resource, and the credential kind (a human session versus
  an API key) that the operation requires
- `#[utoipa::path(security(...))]` documents accepted credentials; it does not enforce them
- Use a builder for `AppState` when construction has several fallible steps

## Middleware and layer placement

In Axum 0.8, `.layer()` and `.route_layer()` wrap only the routes registered **before** the call.
A route added afterwards is not covered. Neither is "global" unless it is called last.

- `.route_layer(l)` runs `l` only for requests that match one of those routes, so an unknown path
  still gets the router's 404 rather than, say, a 401 from an auth layer. Use it for route guards.
- `.layer(l)` wraps those routes and the router's fallback. Use it for cross-cutting concerns such as
  tracing, request IDs, and compression, applied after every route is registered.
- Order: `.layer(a).layer(b)` makes `b` the outer layer, so a request passes through `b` then `a`.
  `ServiceBuilder::new().layer(a).layer(b)` is the reverse: a request passes through `a` then `b`.
  Converting one style into the other without reversing the list inverts the order.

```rust
let protected = Router::new()
    .route("/workspaces", get(workspace::list).post(workspace::create))
    .route_layer(middleware::from_fn_with_state(state.clone(), auth_middleware));

let activation = Router::new()
    .typed_get(oauth::device::activate)
    .typed_post(oauth::device::activate_submit)
    .route_layer(middleware::from_fn_with_state(state.clone(), rate_limit_middleware));

let app = Router::new()
    .merge(protected)
    .merge(activation)
    .route("/regions", get(region::list)) // public, no route guard
    // Applied last, so these wrap every route above. TraceLayer is outermost.
    .layer(middleware::from_fn_with_state(state.clone(), otel_middleware))
    .layer(TraceLayer::new_for_http().make_span_with(HttpMakeSpan))
    .with_state(state);
```

Grouping public and protected routers like this makes the boundary visible, but an existing
router that is already correct does not need restructuring to add a route: find the right
mounting point and add it there.

```rust
pub(crate) async fn auth_middleware(
    State(app): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, AuthError> {
    let token = bearer_token(req.headers())?;
    let principal = app.auth.authenticate(token).await?;
    req.extensions_mut().insert(principal);
    Ok(next.run(req).await)
}
```

Rules:
- Locate the mounting point before adding a handler; a route outside the auth layer is public
- A route outside the shared auth layer can still authenticate inside its own flow (for example
  a credential exchange); "public" means "not gated by that layer", not "unauthenticated"
- `from_fn_with_state` for middleware that needs `AppState`; insert per-request data with
  `req.extensions_mut().insert(...)`
- Choose body limits, timeouts, and concurrency limits per operation and test what callers
  receive; a timeout raises the question of which writes or spawned tasks keep running

## Tracing

### HTTP request spans

Record the matched route template, not the raw path. `request.uri().path()` puts every path
parameter, such as `/oauth/device/confirm/ABCD-1234`, into the span. Read `MatchedPath` from the
request extensions and use a fixed value when no route matched:

```rust
impl<B> MakeSpan<B> for HttpMakeSpan {
    fn make_span(&mut self, request: &Request<B>) -> Span {
        let route = request
            .extensions()
            .get::<MatchedPath>()
            .map(MatchedPath::as_str)
            .unwrap_or("NOT_MATCHED");
        tracing::info_span!("http_request", method = %request.method(), route)
    }
}
```

`MatchedPath` is set during routing, so it is visible to layers added with `Router::layer` but
not to layers wrapped around the router from outside (for example a `ServiceBuilder` applied to
the finished service). Confirm it is present at the layer you change, including for nested and
merged routers. Keep the method, status, latency, and correlation fields that support diagnosis.

### Handler spans

Add `#[instrument]` to handlers. Prefer `skip_all` and name the safe fields you want:

```rust
#[instrument(err, skip_all, fields(%workspace_id))]
pub async fn create(
    ForWorkspace(workspace_id): ForWorkspace,
    WriteDb(db): WriteDb,
    AuthN(auth): AuthN,
    Json(request): Json<CreateRequest>,
) -> Result<JsonResponse<CreateResponse>, ApiError> { ... }

#[instrument(err(Debug), skip_all)]
pub(crate) async fn auth_middleware(...) -> Result<Response, AuthError> { ... }
```

Rules:
- Without `skip_all`, every argument not in `skip(...)` is recorded with `Debug`, including
  bodies; adding a parameter later silently adds a field
- `ret` and `err` are separate decisions: skipping arguments does not stop them recording the
  return value or error. Use `ret` only when the return type's `Debug` is known to be safe (a
  wrapper that deliberately prints no contents). Never use it on a `Redirect`, a raw string, or a
  type that can contain a URL with a code or token in it
- `?value`, `%value`, and formatting a URL that contains the value are three different exposures;
  a type with redacted `Debug` can still leak through its `Display` or through a URL built from it
- Test the property: capture spans and events with a synthetic marker in the sensitive value and
  assert it is absent (see [Testing](#testing))

## Async and Tokio

- Do not hold a synchronous lock guard across `.await`. A short uncontended `std` mutex section
  is fine; use an async mutex only when the resource is genuinely held across awaits
- Keep blocking I/O and long CPU work off the async workers, using the service's existing
  `spawn_blocking` or pool integration; a blocking task keeps running after its caller gives up
- When changing startup or background workers, identify the shutdown signal, how it reaches each
  worker, and who waits for them to drain, and reuse the service's existing handles

## OpenAPI documentation with utoipa

Every public API handler gets a `#[utoipa::path(...)]` annotation above its `#[instrument(...)]`
and must also be listed in its module's `routes!` macro, or it silently drops out of the spec.
Before adding or changing a public endpoint, read [references/openapi.md](references/openapi.md)
for handler annotations, `IntoParams` and `ToSchema`, wire naming, route registration alongside
`TypedPath`, spec assembly, and spec tests.

## Testing

Test through the mounted application, not only by calling handlers directly: a direct call skips
routing, layers, extractors, and rejections, which is where most of the behavior above lives.
Use `tower::ServiceExt::oneshot` on the built `Router`, or the project's harness that runs the
server on an ephemeral port.

For a changed endpoint, cover what applies:

- **Access boundary:** authorized success, unauthenticated (401), authenticated but forbidden
  (403), another tenant's resource, the wrong credential kind, a route meant to be public, and an
  unknown path (404, not 401)
- **Request contract:** wrong content type, malformed body, and wrong field types, compared with
  the statuses and bodies the endpoint promised; protocol-specific rejections such as OAuth forms
- **Body limits:** stream a body without `Content-Length` past a small test limit and expect 413;
  prove extraction stopped early (a poll counter or a detectable later chunk), because a status
  assertion alone passes an implementation that drains the whole stream first
- **No leakage:** put a synthetic marker in a credential field, a body, and a path parameter;
  capture spans and events at debug level and assert the marker is absent, with a positive
  control proving the subscriber captured events from that target
- **Spec:** extend the OpenAPI and typed-path tests in [references/openapi.md](references/openapi.md)

Use synthetic credentials and local fixtures throughout.
