# Clean Code and PEP 8

- **Domain:** `coding_standards`
- **Tags:** `clean-code`, `pep8`, `maintainability`, `python`, `readability`
- **Scope:** Python application and library code.

## Rule [CODE-NAM-01] — Use intention-revealing names

- **Severity:** medium
- **Tags:** `naming`, `readability`
- **Requirement:** Name modules, classes, functions, and variables after the domain concept or action they represent. Use `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Avoid unexplained abbreviations and names such as `data`, `tmp`, or `do_it`.
- **Rationale:** Precise names reduce the amount of context a reader must hold and make reviews and maintenance safer.
- **Examples:** Prefer `calculate_invoice_total(items)` over `calc(x)` and `MAX_RETRY_COUNT` over `limit`.

## Rule [CODE-FUN-01] — Keep functions focused and small

- **Severity:** medium
- **Tags:** `functions`, `single-responsibility`, `complexity`
- **Requirement:** A function should perform one coherent operation, normally fit on one screen, and have a small parameter list. Extract helpers when a function mixes validation, persistence, formatting, and transport concerns.
- **Rationale:** Focused functions are easier to test, reuse, and reason about.
- **Examples:** Separate `validate_order`, `save_order`, and `format_order_response` instead of combining all three in a route handler.

## Rule [CODE-CPLX-01] — Control cyclomatic complexity

- **Severity:** high
- **Tags:** `complexity`, `branching`, `maintainability`
- **Requirement:** Keep cyclomatic complexity at or below 10 per function unless a documented exception is approved. Replace deeply nested conditionals with guard clauses, polymorphism, or small decision functions.
- **Rationale:** High branching complexity increases missed paths and makes adequate testing difficult.
- **Examples:** Return early for invalid inputs rather than nesting the complete success path inside multiple `if` statements.

## Rule [CODE-TYP-01] — Make interfaces and data types explicit

- **Severity:** medium
- **Tags:** `typing`, `interfaces`, `contracts`
- **Requirement:** Add type annotations to public functions, return values, class attributes, and non-obvious local values. Use precise types rather than `Any`; model optional values explicitly and keep annotations accurate.
- **Rationale:** Types document contracts and allow static tools to identify invalid calls before runtime.
- **Examples:** Use `def find_user(user_id: int) -> User | None:` rather than an untyped function returning an ambiguous value.

## Rule [CODE-FMT-01] — Follow consistent formatting

- **Severity:** low
- **Tags:** `pep8`, `formatting`, `imports`
- **Requirement:** Follow PEP 8, use four-space indentation, keep lines within the project formatter limit, group imports consistently, and avoid trailing whitespace. Let an automated formatter enforce details where available.
- **Rationale:** Consistent formatting keeps reviews focused on behavior rather than layout.
- **Examples:** Use one import style throughout a module and do not mix tabs and spaces.