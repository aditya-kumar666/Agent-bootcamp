# OWASP Top 10 Security Guidelines

- **Domain:** `security_owasp`
- **Tags:** `owasp`, `security`, `application-security`, `input-validation`
- **Scope:** Services that process untrusted users, requests, files, or external data.

## Rule [SEC-INJ-01] — Prevent SQL and command injection

- **Severity:** critical
- **Tags:** `injection`, `sql`, `command-execution`
- **Requirement:** Use parameterized queries or a safe query builder for SQL. Pass arguments as an argument list to process APIs and never concatenate untrusted input into SQL, shell commands, templates, or interpreters.
- **Rationale:** Interpolation lets attackers change the intended operation and access or modify data.
- **Examples:** Prefer `WHERE id = ?` with bound parameters over `f"... WHERE id = {user_id}"`; avoid `shell=True` for request-derived input.

## Rule [SEC-SECRET-01] — Do not hardcode secrets

- **Severity:** critical
- **Tags:** `secrets`, `credentials`, `configuration`
- **Requirement:** Keep passwords, API keys, signing keys, and tokens outside source control. Load them from a managed secret store or environment configuration, redact them from logs, and rotate exposed credentials.
- **Rationale:** Source code and logs are frequently copied, indexed, and shared beyond the intended trust boundary.
- **Examples:** Read `DATABASE_URL` from configuration; never commit a real password or token in a default constant.

## Rule [SEC-AUTH-01] — Enforce authentication and authorization server-side

- **Severity:** critical
- **Tags:** `authentication`, `authorization`, `access-control`
- **Requirement:** Verify identity on every protected operation and authorize the authenticated principal against the specific resource and action. Deny by default and do not trust client-supplied roles or ownership fields.
- **Rationale:** UI checks and client claims can be bypassed by direct requests.
- **Examples:** Check that the current user owns an order before returning it, not merely that an `order_id` was supplied.

## Rule [SEC-INPUT-01] — Validate and constrain untrusted input

- **Severity:** high
- **Tags:** `validation`, `sanitization`, `dos`
- **Requirement:** Validate type, shape, length, range, encoding, and allowed values at the trust boundary. Reject invalid input; apply size and rate limits where input can consume meaningful resources. Encode output for its destination context.
- **Rationale:** Validation reduces parser abuse, injection opportunities, and resource exhaustion.
- **Examples:** Enforce a maximum upload size and an allowlist for sort fields instead of accepting arbitrary SQL fragments.