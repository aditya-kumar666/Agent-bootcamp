# Company Engineering Policies

- **Domain:** `company_standards`
- **Tags:** `company-policy`, `logging`, `reliability`, `dependencies`, `privacy`
- **Scope:** All production services and maintained automation.

## Rule [COMP-LOG-01] — Use structured, privacy-safe logging

- **Severity:** high
- **Tags:** `logging`, `pii`, `observability`
- **Requirement:** Emit structured logs with stable event names and useful context such as request ID, operation, outcome, and duration. Never log passwords, tokens, payment data, or unnecessary personally identifiable information; redact values at the logging boundary.
- **Rationale:** Structured logs support reliable operations while privacy-safe fields reduce exposure risk.
- **Examples:** Log `user_id` only when policy permits and use a correlation ID; never log an authorization header or raw request body by default.

## Rule [COMP-IO-01] — Set timeout budgets on every I/O operation

- **Severity:** critical
- **Tags:** `timeouts`, `reliability`, `network`, `database`
- **Requirement:** Configure explicit connect and operation timeouts for HTTP, database, filesystem, and subprocess I/O. Choose budgets that fit the end-to-end request deadline and handle timeout failures explicitly.
- **Rationale:** Unbounded I/O consumes workers and can cascade into an outage.
- **Examples:** Configure an HTTP client timeout and a database command timeout rather than relying on library defaults.

## Rule [COMP-DEP-01] — Use approved and maintained packages

- **Severity:** high
- **Tags:** `dependencies`, `supply-chain`, `packages`
- **Requirement:** Prefer the standard library and approved packages. Before adding a dependency, verify its license, maintenance activity, security posture, transitive dependencies, and necessity; pin or constrain versions according to repository policy.
- **Rationale:** Every dependency adds supply-chain, maintenance, and operational risk.
- **Examples:** Do not add an unreviewed package to perform a small utility operation already supported by the standard library.

## Rule [COMP-ERR-01] — Fail safely and preserve diagnostic context

- **Severity:** high
- **Tags:** `error-handling`, `reliability`, `logging`
- **Requirement:** Catch exceptions only when the component can recover, translate them at a clear boundary, and retain the original cause for internal diagnostics without exposing implementation details to callers.
- **Rationale:** Silent failures and leaked internals both make incidents harder and less safe to handle.
- **Examples:** Return a safe API error while logging the exception with its cause and correlation ID at the service boundary.