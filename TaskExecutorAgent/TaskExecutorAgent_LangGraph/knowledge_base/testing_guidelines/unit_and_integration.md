# Unit and Integration Testing Guidelines

- **Domain:** `testing_guidelines`
- **Tags:** `testing`, `unit-tests`, `integration-tests`, `quality`
- **Scope:** Automated tests for application behavior and boundaries.

## Rule [TEST-AAA-01] — Structure tests as Arrange, Act, Assert

- **Severity:** low
- **Tags:** `aaa`, `readability`, `test-structure`
- **Requirement:** Set up inputs and dependencies in Arrange, execute one behavior in Act, and verify observable outcomes in Assert. Keep the phases visually distinct and the test focused.
- **Rationale:** AAA makes intent and failure location immediately clear.
- **Examples:** Build a user in Arrange, call `register_user` in Act, then assert the returned ID and repository call in Assert.

## Rule [TEST-MOCK-01] — Isolate unit tests with purposeful mocks

- **Severity:** high
- **Tags:** `mocks`, `isolation`, `unit-tests`
- **Requirement:** Unit tests must not call live databases, networks, clocks, or random external services. Replace boundaries with small fakes or mocks and assert meaningful interactions without overspecifying implementation details.
- **Rationale:** Isolation keeps unit tests fast, repeatable, and diagnostic.
- **Examples:** Inject a repository fake into a service test; cover the real database separately in an integration test.

## Rule [TEST-EDGE-01] — Cover important edge and failure cases

- **Severity:** high
- **Tags:** `edge-cases`, `negative-tests`, `coverage`
- **Requirement:** Test valid behavior plus boundary values, empty input, malformed input, missing resources, permission failures, dependency failures, and repeated operations where relevant.
- **Rationale:** Production defects disproportionately occur outside the happy path.
- **Examples:** Test duplicate registration, an empty collection, maximum input length, and repository timeout—not only a valid registration.

## Rule [TEST-DET-01] — Keep tests deterministic

- **Severity:** high
- **Tags:** `determinism`, `time`, `randomness`, `cleanup`
- **Requirement:** Control time, randomness, environment variables, filesystem state, and test data. Clean up resources and avoid ordering dependence or sleeps used as synchronization.
- **Rationale:** Flaky tests erode trust and hide real regressions.
- **Examples:** Inject a clock and fixed random seed, and use a temporary directory fixture that is removed after the test.