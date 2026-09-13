# REST API Conventions

- **Domain:** `api_standards`
- **Tags:** `rest`, `http`, `api`, `contracts`, `pagination`
- **Scope:** HTTP/JSON APIs exposed to internal or external consumers.

## Rule [API-RES-01] — Name resources consistently

- **Severity:** medium
- **Tags:** `resources`, `urls`, `rest`
- **Requirement:** Use plural nouns for collection resources, lowercase kebab-case paths, and nesting only when the child cannot exist independently. Use HTTP methods to express actions instead of verbs in ordinary resource paths.
- **Rationale:** Predictable URLs make APIs easier to discover and consume.
- **Examples:** Use `GET /users/{user_id}/orders`, not `/getUserOrders`.

## Rule [API-HTTP-01] — Return semantically correct status codes

- **Severity:** high
- **Tags:** `status-codes`, `http`, `errors`
- **Requirement:** Use `2xx` for successful operations, `201 Created` for creation, `204 No Content` for successful empty responses, `400` for malformed input, `401` for missing/invalid identity, `403` for insufficient permission, `404` for absent resources, and `409` for state conflicts. Do not return `200` for every outcome.
- **Rationale:** Clients, monitoring, and caches use status codes to make reliable decisions.
- **Examples:** Return `404` when a requested user does not exist and `422` only where the API contract explicitly uses it for semantic validation.

## Rule [API-ERR-01] — Use a stable error envelope

- **Severity:** high
- **Tags:** `errors`, `json`, `contracts`
- **Requirement:** Return errors using `{ "error": { "code": "machine_readable_code", "message": "safe human-readable message" } }`. Keep codes stable, do not expose stack traces or secrets, and include request correlation information only through a documented field or header.
- **Rationale:** A stable shape lets clients handle failures without parsing prose.
- **Examples:** Use `{"error":{"code":"invalid_input","message":"email is required"}}` rather than returning an HTML exception page.

## Rule [API-PAGE-01] — Make collection pagination explicit

- **Severity:** medium
- **Tags:** `pagination`, `collections`, `performance`
- **Requirement:** Paginate potentially large collections with documented limits and stable ordering. Return the page metadata or continuation cursor consistently, and cap client-requested page sizes.
- **Rationale:** Unbounded responses create latency, memory, and denial-of-service risks.
- **Examples:** Support `limit` with a maximum and an opaque `next_cursor`; never allow `limit=unbounded`.