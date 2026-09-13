"""Validate the Phase 1 knowledge corpus using only the standard library."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1] / "knowledge_base"
EXPECTED = {
    "coding_standards/clean_code_and_pep8.md",
    "security_owasp/owasp_top_10.md",
    "architecture/principles_and_solid.md",
    "api_standards/rest_api_conventions.md",
    "testing_guidelines/unit_and_integration.md",
    "company_standards/company_policies.md",
}
RULE_PATTERN = re.compile(r"^## Rule \[([A-Z]+(?:-[A-Z0-9]+)+-\d{2})\] — .+$", re.MULTILINE)
REQUIRED_FIELDS = ("- **Severity:**", "- **Tags:**", "- **Requirement:**", "- **Rationale:**", "- **Examples:**")


def validate() -> list[str]:
    errors: list[str] = []
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.md")}
    for missing in sorted(EXPECTED - actual):
        errors.append(f"missing required file: {missing}")
    for unexpected in sorted(actual - EXPECTED):
        errors.append(f"unexpected markdown file: {unexpected}")

    rule_ids: set[str] = set()
    for relative in sorted(EXPECTED & actual):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            errors.append(f"{relative}: missing H1 title")
        if len(re.findall(r"^# (?!#).+$", text, re.MULTILINE)) != 1:
            errors.append(f"{relative}: expected exactly one H1 title")
        if not re.search(r"^- \*\*Domain:\*\* `[^`]+`$", text, re.MULTILINE):
            errors.append(f"{relative}: missing Domain metadata")
        if not re.search(r"^- \*\*Tags:\*\* `[^`]+`(?:, `[^`]+`)*$", text, re.MULTILINE):
            errors.append(f"{relative}: missing or malformed Tags metadata")
        rules = RULE_PATTERN.findall(text)
        if not rules:
            errors.append(f"{relative}: no valid rule headings")
        for rule_id in rules:
            if rule_id in rule_ids:
                errors.append(f"duplicate rule ID: {rule_id}")
            rule_ids.add(rule_id)
        sections = re.split(r"^## Rule \[.*?$", text, flags=re.MULTILINE)[1:]
        for index, section in enumerate(sections, 1):
            for field in REQUIRED_FIELDS:
                if not re.search(rf"^{re.escape(field)} .+$", section, re.MULTILINE):
                    errors.append(f"{relative}: rule {index} missing {field[:-1]}")
    if len(rule_ids) < 20:
        errors.append(f"expected at least 20 rules, found {len(rule_ids)}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Knowledge base validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Knowledge base validation passed: {len(EXPECTED)} files, {len(_all_rule_ids())} rules.")
    return 0


def _all_rule_ids() -> set[str]:
    return {rule for path in ROOT.rglob("*.md") for rule in RULE_PATTERN.findall(path.read_text(encoding="utf-8"))}


if __name__ == "__main__":
    raise SystemExit(main())