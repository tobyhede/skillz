---
name: rust-axum
description: Apply when building or modifying Axum HTTP services, handlers, middleware, or extractors. TRIGGER when creating or editing Axum route handlers, defining error types that implement IntoResponse, writing middleware functions, building custom extractors (FromRequest/FromRequestParts), configuring Router, or structuring AppState. DO NOT TRIGGER when writing library/SDK code with no HTTP layer, pure domain logic, CLI tools, or non-Rust files.
user-invocable: false
---

# Axum Service Development

When building Axum HTTP services, follow these conventions to produce consistent, observable, and
well-structured web applications.

## RESTful Routes & TypedPath

Use `axum_extra::routing::TypedPath` for compile-time route checking. Define routes as unit or tuple
structs with `#[typed_path("/path")]`.

```rust
use axum_extra::routing::TypedPath;
use serde::Deserialize;

// Unit struct for routes with no parameters
#[derive(Debug, TypedPath, Deserialize)]
#[typed_path("/oauth/device/token")]
pub struct DeviceTokenPath;

// Struct with parameters for dynamic routes
#[derive(Debug, TypedPath, Deserialize)]
#[typed_path("/oauth/device/confirm/{user_code}")]
pub struct ConfirmPath {
    user_code: UserCode,
}
```

Use `.to_uri()` for building redirect URLs and `state.url_for(path)` for full URL construction:

```rust
// Redirect using TypedPath — compile-time checked route
let dest = ActivatePath
    .with_query_params(user_code_param)
    .to_uri()
    .to_string();
Redirect::to(&dest)

// Full URL from state — uses base_url + typed path
let callback_url = state.url_for(PkceCallbackPath)?;
```

Register typed routes with `.typed_get()` / `.typed_post()` on the router:

```rust
let router = Router::new()
    .typed_post(oauth::device::token)
    .typed_get(oauth::device::activate)
    .typed_post(oauth::pkce::start)
    // Standard routes for simpler cases
    .route("/health", get(async || StatusCode::OK))
    .route("/workspaces", get(workspace::list))
    .route("/workspaces", post(workspace::create));
```

Rules:
- RESTful naming: plural nouns (`/workspaces`, `/memberships`), standard HTTP methods
- TypedPath handler's first parameter is the path struct (e.g. `_: DeviceTokenPath`)
- Use `.to_uri()` for redirects — never hardcode route strings
- `state.url_for(path)` for absolute URLs (e.g. OAuth callbacks, email links)
- `state.path_for(path)` when you only need the path segment without the base URL

## Error Handling — Layered Pattern

Structure errors in three tiers:

### 1. Domain errors — granular, internal

Fine-grained `thiserror` enums listing every possible failure. These live in domain crates and are
never exposed directly to HTTP clients.

```rust
// domain/src/oauth/mod.rs
#[derive(Debug, thiserror::Error)]
pub enum DeviceAuthRequestError {
    #[error("Failed to generate user code: {0}")]
    UserCodeGenerationFailed(#[from] RandomError),

    #[error("Missing config: {0}")]
    ConfigMissing(String),

    #[error("Storage error: {0}")]
    StorageError(#[from] DeviceCodeError),
}
```

### 2. User-facing errors — coarse, safe for HTTP

Fewer variants with `IntoResponse` and status code mapping. These are what clients see.

```rust
// domain/src/oauth/error.rs
#[derive(Debug, Clone, thiserror::Error)]
pub enum Error {
    #[error("An invalid request was made")]
    InvalidRequest,

    #[error("The client ID is invalid or not authorized")]
    InvalidClient,

    #[error("An internal error occurred")]
    ServerError,
}

impl Error {
    pub fn status_code(&self) -> StatusCode {
        match self {
            Self::InvalidRequest | Self::InvalidClient => StatusCode::BAD_REQUEST,
            Self::ServerError => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}
```

### 3. Conversion — erase details, log internally

`From<DomainError> for UserError` maps granular errors to coarse ones.
Use `inspect_err` + `tracing::error!` to preserve internal observability.

```rust
// Domain error → user-facing error (detail erasure)
impl From<DeviceAuthRequestError> for oauth::Error {
    fn from(_: DeviceAuthRequestError) -> Self {
        oauth::Error::ServerError
    }
}

// In handlers — inspect_err for logging, map_err for user-facing response
let claims = verify_service_token(token, &auth.jwk_manager())
    .await
    .inspect_err(|e| tracing::warn!("{e}"))
    .map_err(|_| AuthError::Unauthorized("Unauthorized"))?;
```

Rules:
- Domain errors are detailed and include `#[from]` for upstream errors
- User-facing errors are coarse — never leak internal details, paths, or stack traces
- `From` conversions always erase details (use `_` for the source error)
- `inspect_err` logs the real error; `map_err` returns a generic one to the client

## IntoResponse for Error Types

Implement `IntoResponse` only on user-facing error types. Map variants to status codes and serialize
as JSON.

```rust
impl IntoResponse for Error {
    fn into_response(self) -> Response {
        (self.status_code(), Json(self)).into_response()
    }
}
```

For domain errors from other crates that need `IntoResponse` in the web layer, use the
`ErrorResponse<T>` newtype wrapper:

```rust
// web/src/lib.rs — wraps external error types for IntoResponse
#[derive(Debug)]
pub struct ErrorResponse<T>(T);
```

For auth middleware errors that don't need JSON bodies, use tuple responses:

```rust
#[derive(Debug)]
pub(crate) enum AuthError {
    Unauthorized(&'static str),
    BadRequest(&'static str),
    Internal,
}

impl IntoResponse for AuthError {
    fn into_response(self) -> Response {
        match self {
            AuthError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, msg).into_response(),
            AuthError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg).into_response(),
            AuthError::Internal => {
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error").into_response()
            }
        }
    }
}
```

Rules:
- Only user-facing error types implement `IntoResponse`
- Domain errors never implement `IntoResponse` directly
- JSON errors: `(status, Json(self)).into_response()`
- Plain text errors: `(status, message).into_response()`
- Use `ErrorResponse<T>` to bridge external domain errors into the web layer

## JSON Responses

Use `JsonResponse<T>` for consistent JSON responses with status code control. Use `JsonResult<T, E>`
as the handler return type.

```rust
// Type alias for handler returns
pub type JsonResult<T, E> = Result<JsonResponse<T>, E>;

// In handlers — return JsonResponse with optional status
pub async fn token(
    _: DeviceTokenPath,
    State(state): State<AppState>,
    WriteDb(db): WriteDb,
    Form(request): Form<DeviceTokenRequest>,
) -> JsonResult<DeviceTokenResponse, oauth::Error> {
    // ...
    Ok(JsonResponse::new(DeviceTokenResponse {
        access_token: signed.token,
        token_type: "Bearer",
        expires_in,
    }))
}

// Override the default 200 status
JsonResponse::new(response).with_status(StatusCode::CREATED)
```

For error messages, use the `json_error_message` helper:

```rust
JsonResponse::new(json_error_message("Failed to get a connection from the pool"))
    .with_status(StatusCode::INTERNAL_SERVER_ERROR)
```

## Extractors Over Extensions

Use custom `FromRequest` / `FromRequestParts` implementations instead of `Extension<T>`. Extensions
are not statically checked — a missing extension silently causes a runtime error.

```rust
// GOOD — custom extractor, statically checked
pub struct ReadDb(pub PgConn);

impl FromRequestParts<AppState> for ReadDb {
    type Rejection = JsonResponse<ErrorMessage<'static>>;

    async fn from_request_parts(
        _parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        let dual_pool = DualPool::from_ref(state);
        PgConn::checkout(dual_pool.for_read())
            .await
            .map_err(pool_get_failed)
            .map(ReadDb)
    }
}

// GOOD — role-based access via extractor
pub struct WorkspaceRole<S = ()>(pub WorkspaceId, pub S);

// BAD — Extension is not statically verified
async fn handler(Extension(db): Extension<PgConn>) -> ... { }
```

Typical extractor set for a service:
- `ReadDb` / `WriteDb` — database connections from read-replica or primary pool
- `BearerToken` — extracts the `Authorization: Bearer <token>` header
- `ForWorkspace` — extracts workspace ID from the authenticated user
- `WorkspaceRole<AdminRole>` — workspace ID with role enforcement
- `HasPermission<P>` — generic permission check via `PermissionCheck` trait
- `AuthN` — extracts the `Authorization` instance from state

## Handle Request Parsing Safely

Never destructure `Json<T>` directly in handler parameters — deserialization errors produce poor
default responses. Use `StrictJson<T>` or handle the rejection explicitly.

```rust
// GOOD — StrictJson logs deserialization errors
pub struct StrictJson<T>(pub T);

impl<T, S> FromRequest<S> for StrictJson<T>
where
    T: DeserializeOwned + Debug,
    S: Send + Sync,
{
    type Rejection = <Json<T> as FromRequest<S>>::Rejection;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        let (parts, body) = req.into_parts();
        let bytes = buffer_and_print("request", body).await.unwrap();
        let req = Request::from_parts(parts, Body::from(bytes));

        Json::<T>::from_request(req, state)
            .await
            .map(|Json(value)| StrictJson(value))
            .inspect_err(|err| {
                tracing::error!("Failed to deserialize JSON: {}", err);
            })
    }
}

// GOOD — Form extraction with typed path
pub async fn token(
    _: DeviceTokenPath,
    State(state): State<AppState>,
    WriteDb(db): WriteDb,
    Form(request): Form<DeviceTokenRequest>,
) -> JsonResult<DeviceTokenResponse, oauth::Error> { ... }
```

Rules:
- Use `StrictJson<T>` instead of `Json<T>` for request bodies
- Always log deserialization failures — they indicate client bugs or attacks
- For form data, `Form<T>` is fine as-is since form parsing errors are less ambiguous

## Handler Instrumentation

Add `#[instrument(...)]` to every handler for tracing. Skip sensitive extractors.

```rust
// Standard pattern — err + ret, skip db/auth/request bodies
#[instrument(err, ret, skip(db, auth))]
pub async fn create(
    ForWorkspace(workspace_id): ForWorkspace,
    WriteDb(db): WriteDb,
    AuthN(auth): AuthN,
    StrictJson(request): StrictJson<CreateRequest>,
) -> JsonResult<CreateResponse, Error> { ... }

// skip_all with explicit fields — for handlers with many params
#[instrument(err, ret, skip_all, fields(member_id = %user.id, external_id = %user.external_id))]
pub async fn delete(
    Extension(user): Extension<Arc<User>>,
    WriteDb(db): WriteDb,
    Path(params): Path<DeleteParams>,
) -> Result<impl IntoResponse, Error> { ... }

// Middleware — skip_all is required (no useful params to log)
#[instrument(err(Debug), skip_all)]
pub(crate) async fn auth_middleware(
    State(app): State<AppState>,
    req: Request,
    next: Next,
) -> Result<impl IntoResponse, AuthError> { ... }

// Light handlers — skip specific param, add fields
#[instrument(ret, skip(user_code_param), fields(user_code = ?user_code_param.user_code))]
pub async fn activate_submit(
    _: ActivatePath,
    Form(user_code_param): Form<UserCodeParam>,
) -> Redirect { ... }
```

Rules:
- `err` — logs the error if the handler returns `Err`
- `ret` — logs the return value (works with `TracedResponse` which redacts contents)
- `skip(db, auth, conn, request)` — always skip database connections, auth objects, and request bodies
- `skip_all` + `fields(...)` — when there are many params or you need to control exactly what's logged
- `err(Debug)` — for middleware where the error type's `Debug` is more useful than `Display`

## Middleware Patterns

Use `axum::middleware::from_fn_with_state` for middleware that needs access to application state.
Use `.route_layer()` for scoped middleware and `.layer()` for global middleware.

```rust
// Scoped middleware — only applies to routes above it
let router = OpenApiRouter::new()
    .route("/workspaces", get(workspace::list))
    .route("/workspaces", post(workspace::create))
    // Auth middleware applies to all routes above
    .route_layer(axum::middleware::from_fn_with_state(
        state.clone(),
        auth_middleware,
    ))
    // Public routes below are NOT affected by auth
    .route("/regions", get(region::list));

// Separate router for specific middleware (e.g. rate limiting)
let activate_router = Router::new()
    .typed_get(oauth::device::activate)
    .typed_post(oauth::device::activate_submit)
    .route_layer(axum::middleware::from_fn_with_state(
        state.clone(),
        rate_limit_middleware,
    ))
    .with_state(state.clone());

let router = router.merge(activate_router);

// Global middleware — applied to all routes via .layer()
let router = router
    .layer(axum::middleware::from_fn_with_state(
        state.tracer(),
        otel_middleware,
    ))
    .layer(
        TraceLayer::new_for_http()
            .make_span_with(HttpMakeSpan)
            .on_request(HttpOnRequest)
            .on_response(HttpOnResponse),
    )
    .with_state(state);
```

Middleware function signature:

```rust
pub(crate) async fn auth_middleware(
    State(app): State<AppState>,
    req: Request,
    next: Next,
) -> Result<impl IntoResponse, AuthError> {
    // Extract and validate
    let token = extract_bearer_token(&req)?;

    // Modify request (e.g. add extensions)
    let user = authenticate(token).await?;
    req.extensions_mut().insert(Arc::new(user));

    // Call next
    Ok(next.run(req).await)
}
```

Rules:
- `.route_layer()` — scoped: applies only to routes defined above it in the chain
- `.layer()` — global: applies to all routes
- `from_fn_with_state` — middleware that needs `AppState`
- Middleware returns `Result<impl IntoResponse, Error>`
- Insert per-request data via `req.extensions_mut().insert(...)` for downstream handlers

## State Management

Use a `Clone`-able `AppState` struct with `FromRef` for sub-state decomposition.

```rust
#[derive(Clone)]
pub struct AppState {
    pub base_url: Url,
    pub auth: Authorization,
    pub config: Arc<Config>,
    pub dual_pool: DualPool,
    pub tracer: Option<Arc<Tracer>>,
    pub activate_rate_limiter: RateLimiter,
}

// FromRef — lets extractors access sub-state without knowing about AppState
impl FromRef<AppState> for DualPool {
    fn from_ref(state: &AppState) -> Self {
        state.dual_pool.clone()
    }
}

impl FromRef<AppState> for RateLimiter {
    fn from_ref(state: &AppState) -> Self {
        state.activate_rate_limiter.clone()
    }
}
```

Use a builder for `AppState` construction:

```rust
impl AppState {
    pub async fn build(config: Config) -> Result<Self, anyhow::Error> {
        AppStateBuilder::new(config).build().await
    }
}
```

Rules:
- `AppState` must implement `Clone` (Axum requirement)
- Wrap large or non-Clone fields in `Arc<T>`
- Use `FromRef` so extractors can access sub-state independently — avoids tight coupling
- Builder pattern for construction when there are multiple initialization steps
- Helper methods on `AppState` for common operations (`url_for`, `authorization`, etc.)

## OpenAPI Documentation with utoipa

Every public API handler gets a `#[utoipa::path(...)]` annotation above its `#[instrument(...)]`
and must also be listed in its module's `routes!` macro, or it silently drops out of the spec.
Before adding or changing a public endpoint, read [references/openapi.md](references/openapi.md)
for handler annotations, `ToSchema` and `ToParam`, extractor params, route registration, and
spec assembly.
