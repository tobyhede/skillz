# OpenAPI documentation with utoipa

Read this when adding or changing a public API endpoint that must appear in the OpenAPI spec.

## Contents

- [Annotating handlers](#annotating-handlers)
- [Schema types](#schema-types)
- [Parameters: `IntoParams`, inline `params`, and `ToSchema`](#parameters-intoparams-inline-params-and-toschema)
- [Route registration with `routes!`](#route-registration-with-routes)
- [Typed paths alongside `routes!`](#typed-paths-alongside-routes)
- [App-level OpenAPI assembly](#app-level-openapi-assembly)
- [Building the OpenAPI spec](#building-the-openapi-spec)
- [Rules](#rules)
- [Testing the spec](#testing-the-spec)

Use `utoipa` and `utoipa_axum` to generate OpenAPI specs from handler annotations. Docs are
served via `utoipa_scalar`. The examples target utoipa 5 and utoipa-axum 0.2; check derive and
macro names against the versions in the project's `Cargo.lock`.

A spec describes the API; it enforces nothing. `security(...)` on an operation documents which
credentials a caller may present, but the gate is the middleware and extractors on the route.
When the two disagree (an operation advertises a credential that the handler always rejects),
fix the spec and add an assertion for it, and leave the runtime check alone.

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
logic and should NOT appear in `params()` — they are not part of the API contract. Listing a
security scheme does not make the handler check it; see the note at the top of this file.

## Schema types

Derive `ToSchema` on all request and response types and use doc comments for field
descriptions. Follow the wire names the API already uses: keep existing `serde` renames, and do
not apply a blanket `rename_all` to a type whose fields follow a protocol (OAuth's
`access_token`, `token_type`, and `expires_in` are snake_case by specification). Renaming a field
on an existing type is a breaking change for clients. The example below is a new type in an API
whose convention is camelCase.

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

## Parameters: `IntoParams`, inline `params`, and `ToSchema`

utoipa has no `ToParam` derive. It provides two:

- `IntoParams` for a type that stands for a group of parameters, such as a query struct or an
  extractor that reads a header. List the type in `params(...)`.
- `ToSchema` for a value that has a schema, whether it travels in a body or is the type of a
  parameter. An enum used as a path or query parameter still derives `ToSchema`.

```rust
// Body type → ToSchema
#[derive(Debug, Serialize, ToSchema)]
pub struct ProvidersResponse(Vec<OidcProvider>);

// Value type of a path or query parameter → ToSchema, so the parameter can reference it
#[derive(Debug, Deserialize, ToSchema)]
#[serde(rename_all = "lowercase")]
pub enum OidcVendor {
    Auth0,
    Okta,
}

// A group of query parameters → IntoParams
#[derive(Debug, Deserialize, IntoParams)]
#[into_params(parameter_in = Query)]
pub struct ListProvidersQuery {
    /// Only return providers from this vendor
    vendor: Option<OidcVendor>,
}

// An extractor that reads a header → IntoParams with an explicit name
#[derive(IntoParams)]
#[into_params(names("x-workspace-id"), parameter_in = Header)]
pub(crate) struct ForWorkspace(pub WorkspaceId);
```

A single path, query, or header parameter can be declared inline instead of deriving anything:

```rust
#[utoipa::path(
    get,
    path = "/providers/{vendor}",
    params(
        ("vendor" = OidcVendor, Path, description = "Identity provider vendor"),
        ListProvidersQuery,
    ),
    responses((status = 200, body = ProvidersResponse)),
)]
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

`routes!` reads the `__path_<handler>` item that `#[utoipa::path]` generates next to each
handler. When the handlers live in submodules and `routes!` is called from the parent, re-export
both names; when they are in the same module, no re-export is needed:

```rust
// mod.rs
pub(crate) use create::{__path_create, create};
pub(crate) use delete::{__path_delete, delete};
pub(crate) use list::{__path_list, list};
```

## Typed paths alongside `routes!`

A handler can take a `TypedPath` struct for extraction and link building while `routes!` mounts
it from its `#[utoipa::path]` metadata. The path is then declared twice, once in
`#[typed_path("...")]` and once in `path = "..."`, so keep a test that compares the two for
every such handler and fails when they drift.

A plain `.route()` registration is invisible to the spec. Use that deliberately for a
compatibility alias (for example a second spelling of a path kept for old clients) and note it
beside the route, so a later change neither documents nor deletes it by accident.

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
                .security_scheme("jwt", SecurityScheme::Http(
                    HttpBuilder::new()
                        .scheme(HttpAuthScheme::Bearer)
                        .bearer_format("JWT")
                        .build(),
                ))
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

## Rules

- Every public API handler gets a `#[utoipa::path(...)]` annotation
- The `tag` should reference a module-level `OPENAPI_TAG` constant
- `#[utoipa::path]` goes above `#[instrument]` in attribute order
- Derive `ToSchema` on all request/response structs, keeping the API's existing wire names
- Use doc comments on handler functions — they become the OpenAPI operation summary and description
- Use `#[schema(examples(...))]` for field-level examples in the spec
- Use `#[cfg_attr(test, derive(Deserialize))]` on response-only types that need deserialization in tests
- Security schemes defined once in `build_api_doc`, referenced by name in handler annotations
- Error responses can omit `body` — `(status = 401)` is valid when the error shape varies or is handled by middleware
- Doc comment first line = endpoint heading in rendered docs; must be followed by a blank `///` line
- Derive `IntoParams` for parameter groups, declare single parameters inline in `params(...)`, and derive `ToSchema` on the value types they reference; `ToParam` does not exist
- `params()` is only for API parameters — never include auth extractors like `HasPermission` or `WorkspaceRole`
- Both `#[utoipa::path()]` and `routes!` registration are required for a handler to appear in the spec
- `security(...)` documents credentials; the route's middleware and extractors enforce them

## Testing the spec

- Fetch `/api/openapi.json` from the assembled app in a test and assert on the operations,
  parameters, responses, and security alternatives you changed, so a missing `routes!` entry or
  a stale annotation fails the build.
- Keep the typed-path agreement test from [Typed paths alongside `routes!`](#typed-paths-alongside-routes)
  up to date when you add or rename a route.
- To read the rendered docs locally, turn on the service's `serve_openapi_docs` setting (for
  example `APP__SERVE_OPENAPI_DOCS=true` in your environment or `mise.toml`) and open
  `http://localhost:3001/openapi`.
