# Architecture Principles and SOLID

- **Domain:** `architecture`
- **Tags:** `solid`, `layered-architecture`, `coupling`, `dependencies`, `design`
- **Scope:** Multi-module services and libraries.

## Rule [ARCH-SOLID-01] — Apply single responsibility

- **Severity:** medium
- **Tags:** `solid`, `srp`, `cohesion`
- **Requirement:** Give each module or class one cohesive reason to change. Keep transport, business policy, persistence, and presentation responsibilities separate.
- **Rationale:** Cohesive components are easier to change without causing unrelated regressions.
- **Examples:** A repository should persist data; it should not also parse HTTP requests or render HTML.

## Rule [ARCH-SOLID-02] — Depend on abstractions at boundaries

- **Severity:** medium
- **Tags:** `solid`, `dependency-inversion`, `interfaces`
- **Requirement:** Business logic should depend on stable interfaces or protocols rather than concrete databases, frameworks, or network clients. Inject infrastructure dependencies at composition boundaries.
- **Rationale:** Dependency inversion improves test isolation and permits infrastructure changes.
- **Examples:** Inject a `UserRepository` protocol into a service rather than constructing a concrete database client inside the service.

## Rule [ARCH-LAYER-01] — Preserve one-way layer boundaries

- **Severity:** high
- **Tags:** `layers`, `boundaries`, `coupling`
- **Requirement:** Keep dependencies flowing from delivery to application/domain logic to infrastructure. Lower-level infrastructure must not import route handlers or UI concerns.
- **Rationale:** One-way dependencies prevent hidden coupling and make execution paths understandable.
- **Examples:** A controller calls an application service; the repository does not call the controller.

## Rule [ARCH-DEP-01] — Avoid circular dependencies

- **Severity:** high
- **Tags:** `dependencies`, `cycles`, `modularity`
- **Requirement:** Do not create import or package cycles. Move shared contracts to a neutral module, invert the dependency, or introduce an explicit coordinator when two components require each other.
- **Rationale:** Cycles complicate initialization, testing, deployment, and future refactoring.
- **Examples:** Put shared DTOs in `models` rather than making `services` and `repositories` import each other.