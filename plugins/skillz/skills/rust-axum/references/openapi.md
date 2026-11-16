# OpenAPI documentation with utoipa

Read this when adding or changing a public API endpoint that must appear in the OpenAPI spec.

## Contents

- [Annotating handlers](#annotating-handlers)
- [Schema types](#schema-types)
- [`ToSchema` vs `ToParam`](#toschema-vs-toparam)
- [Extractor params](#extractor-params)
- [Route registration with `routes!`](#route-registration-with-routes)
- [App-level OpenAPI assembly](#app-level-openapi-assembly)
- [Building the OpenAPI spec](#building-the-openapi-spec)
- [Local testing](#local-testing)

Use `utoipa` and `utoipa_axum` to generate OpenAPI specs from handler annotations. Docs are
served via `utoipa_scalar`.

## Annotating handlers

Add `#[utoipa::path(...)]` above each handler's `#[instrument(...)]`. Specify the HTTP method,
path, tag, request/response types, and security schemes.

Doc comments on handlers flow into the OpenAPI spec: the **first line** becomes the endpoint
heading in rendered docs and must be followed by a blank `///` line. Subsequent lines become the
description. Type-level doc comments also appear in the public API docs — write them with end
users in mind, not internal developers.

```rust
/// Create Access Key
///
/// Creates a new access key for the workspace.
/// The authenticated user must have admin privileges in the workspace.
#[utoipa::path(
    post,
    path = "/access-keys",
    tag = super::OPENAPI_TAG,
    request_body = CreateAccessKeyRequest,
    responses(
        (status = 201, body = CreateAccessKeyResponse, description = "Access key created successfully"),
        (status = 400, description = "Bad request - invalid parameters or duplicate name"),
        (status = 401, description = "Unauthorized - missing or invalid token"),
        (status = 403, description = "Forbidden - insufficient permissions (requires admin)"),
    ),
    security(
        ("jwt" = []),
        ("access_key" = []),
    )
)]
#[instrument(err, ret, skip_all, fields(%key_name, %workspace_id, ?role))]
pub async fn create(...) -> JsonResult<CreateAccessKeyResponse, AccessKeyHandlerError> { ... }
```

For GET endpoints with query/header parameters, use `params(...)`:

```rust
#[utoipa::path(
    get,
    path = "/access-keys",
    tag = super::OPENAPI_TAG,
    params(ForWorkspace),
    responses(
        (status = 200, body = Vec<AccessKey>),
        (status = 401),
        (status = 403),
    ),
    security(
        ("jwt" = []),
        ("access_key" = []),
    )
)]
pub async fn list(
    Db(db): Db,
    HasPermission(user, ..): HasPermission<ListAccessKeysPermission>,
    ForWorkspace(workspace_id): ForWorkspace,
) -> JsonResult<Vec<AccessKey>, ListAccessKeysError> { ... }
```

Only use `params()` for types representing actual API parameters (headers, query strings, path
segments). Auth extractors like `HasPermission` or `WorkspaceRole` handle internal authorization
logic and should NOT appear in `params()` — they are not part of the API contract.

## Schema types

Derive `ToSchema` on all request and response types. Use `#[serde(rename_all = "camelCase")]` for
JSON field naming and doc comments for field descriptions.

```rust
#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(rename_all = "camelCase")]
pub struct CreateAccessKeyRequest {
    /// Name for the new access key
    key_name: String,

    /// The workspace ID where this key should be created
    workspace_id: WorkspaceId,

    /// Optional role for the access key. Defaults to Member if not provided
    role: Option<Role>,
}

// For response types shown in OpenAPI but also used as extractors
#[derive(Debug, Serialize, ToSchema)]
#[cfg_attr(test, derive(Deserialize))]
pub struct RegionWithEndpoint {
    #[schema(examples("us-east-1.aws"))]
    pub(crate) region: Region,

    #[schema(examples("https://us-east-1.api.example.com/"))]
    pub(crate) endpoint: Url,
}
```

## `ToSchema` vs `ToParam`

Use `ToSchema` for types that appear in request/response **bodies**. Use `ToParam` for enums and
types extracted from the URL path, query string, or headers:

```rust
// Body type → ToSchema
#[derive(Debug, Serialize, ToSchema)]
pub struct ProvidersResponse(Vec<OidcProvider>);

// Path/query parameter → ToParam
#[derive(ToParam)]
pub enum OidcVendor {
    Auth0,
    Okta,
}
```

Rule of thumb: if it's in the `body`, derive `ToSchema`. If it's in the URL or headers, derive
`ToParam`.

## Extractor params

Extractors used as OpenAPI parameters implement `IntoParams`:

```rust
#[derive(IntoParams)]
#[into_params(names("x-workspace-id"), parameter_in = Header)]
pub(crate) struct ForWorkspace(pub WorkspaceId);
```

## Route registration with `routes!`

Group related handlers into a `router()` function using the `routes!` macro from `utoipa_axum`.
This auto-registers both the route and its OpenAPI metadata.

```rust
use utoipa_axum::{router::UtoipaMethodRouter, routes};

pub(crate) const OPENAPI_TAG: &str = "Access Keys";

pub(crate) fn router() -> UtoipaMethodRouter<AppState> {
    routes!(list, create, delete)
}
```

A handler must have BOTH `#[utoipa::path()]` AND be listed in `routes!` to appear in the spec.
Missing either one means the endpoint silently won't show up in the docs.

The `routes!` macro generates `__path_<handler>` items that must be re-exported from the module:

```rust
// mod.rs
pub(crate) use create::{__path_create, create};
pub(crate) use delete::{__path_delete, delete};
pub(crate) use list::{__path_list, list};
```

## App-level OpenAPI assembly

Use `OpenApiRouter` to compose routers with their OpenAPI metadata. Register grouped routers
with `.routes()` and individual routes with `.route()`.

```rust
use utoipa_axum::router::OpenApiRouter;
use utoipa_scalar::{Scalar, Servable};

let router = OpenApiRouter::new()
    .routes(access_keys::router())
    .routes(oidc::router())
    .route("/workspaces", get(workspace::list))
    .route_layer(axum::middleware::from_fn_with_state(state.clone(), auth_middleware))
    .routes(region::router())
    .with_state(state.clone());

let (router, api) = OpenApiRouter::with_openapi(build_api_doc(state.clone())?)
    .nest("/api", router)
    .split_for_parts();

// Serve docs at /openapi (conditionally)
let router = if state.config.serve_openapi_docs {
    router.merge(Scalar::with_url("/openapi", api.clone()))
} else {
    router
};

// Always serve the raw spec
router.route("/api/openapi.json", get(|| async { Json(api) }))
```

## Building the OpenAPI spec

Define the API info, servers, and security schemes in a dedicated `open_api.rs` module:

```rust
use utoipa::openapi::{
    security::{HttpAuthScheme, HttpBuilder, SecurityScheme},
    Components, ComponentsBuilder, Info, InfoBuilder, OpenApi, OpenApiBuilder, ServerBuilder,
};

pub(crate) fn build_api_doc(state: AppState) -> anyhow::Result<OpenApi> {
    let server = ServerBuilder::new().url(state.base_url()?).build();

    let openapi = OpenApiBuilder::new()
        .info(InfoBuilder::new()
            .title("Example API")
            .version(env!("CARGO_PKG_VERSION"))
            .build())
        .components(Some(
            ComponentsBuilder::new()
                .security_scheme("access_key", SecurityScheme::Http(
                    HttpBuilder::new().scheme(HttpAuthScheme::Bearer).build(),
                ))
                .build(),
        ))
        .servers(Some(vec![server]))
        .build();

    Ok(openapi)
}
```

Rules:
- Every public API handler gets a `#[utoipa::path(...)]` annotation
- The `tag` should reference a module-level `OPENAPI_TAG` constant
- `#[utoipa::path]` goes above `#[instrument]` in attribute order
- Derive `ToSchema` on all request/response structs
- Use doc comments on handler functions — they become the OpenAPI operation summary and description
- Use `#[schema(examples(...))]` for field-level examples in the spec
- Use `#[cfg_attr(test, derive(Deserialize))]` on response-only types that need deserialization in tests
- Security schemes defined once in `build_api_doc`, referenced by name in handler annotations
- Error responses can omit `body` — `(status = 401)` is valid when the error shape varies or is handled by middleware
- Doc comment first line = endpoint heading in rendered docs; must be followed by a blank `///` line
- Derive `ToParam` (not `ToSchema`) for enums/types used as path, query, or header parameters
- `params()` is only for API parameters — never include auth extractors like `HasPermission` or `WorkspaceRole`
- Both `#[utoipa::path()]` and `routes!` registration are required for a handler to appear in the spec

## Local testing

Turn on the service's `serve_openapi_docs` setting (for example `APP__SERVE_OPENAPI_DOCS=true` in
your environment or `mise.toml`) and open the rendered docs at `http://localhost:3001/openapi`.
