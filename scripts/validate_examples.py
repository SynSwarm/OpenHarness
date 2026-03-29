#!/usr/bin/env python3
"""Validate examples/**/*.json against schema/openharness-v1.draft.json (draft 2020-12)."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schema" / "openharness-v1.draft.json"
    examples_dir = root / "examples"

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print(
            "Missing dependency: pip install jsonschema>=4.20",
            file=sys.stderr,
        )
        return 2

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    paths = sorted(examples_dir.rglob("*.json"))
    if not paths:
        print("No JSON files under examples/", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in paths:
        rel = path.relative_to(root)
        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
            validator.validate(instance)
        except Exception as e:
            errors.append(f"{rel}: {e}")

    if errors:
        print("Schema validation failed:\n", file=sys.stderr)
        for line in errors:
            print(line, file=sys.stderr)
        return 1

    print(f"OK: validated {len(paths)} example JSON file(s) against {schema_path.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
