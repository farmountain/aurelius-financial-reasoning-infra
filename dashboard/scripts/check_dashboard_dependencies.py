#!/usr/bin/env python3
"""Validate dashboard external imports are declared in package.json dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE_JSON = ROOT / "package.json"

IMPORT_PATTERN = re.compile(r"(?:import\s+[^'\"]+from\s+|import\()['\"]([^'\"]+)['\"]")

ALLOWED_UNDECLARED = {
    "react/jsx-runtime",
}

ALLOWED_UNUSED_RUNTIME = {
    "@emotion/react",  # peer dependency for @mui/material
    "@emotion/styled",  # peer dependency for @mui/material
}


def normalize_package_name(module_name: str) -> str:
    if module_name.startswith("@"):
        parts = module_name.split("/")
        return "/".join(parts[:2])
    return module_name.split("/")[0]


def collect_external_imports() -> set[str]:
    imports: set[str] = set()
    for path in SRC.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        for match in IMPORT_PATTERN.findall(text):
            if match.startswith(".") or match.startswith("/"):
                continue
            imports.add(normalize_package_name(match))

    for path in SRC.rglob("*.jsx"):
        text = path.read_text(encoding="utf-8")
        for match in IMPORT_PATTERN.findall(text):
            if match.startswith(".") or match.startswith("/"):
                continue
            imports.add(normalize_package_name(match))

    return imports


def main() -> int:
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    declared = set(package.get("dependencies", {}).keys()) | set(package.get("devDependencies", {}).keys())
    used = collect_external_imports()

    missing = sorted([pkg for pkg in used if pkg not in declared and pkg not in ALLOWED_UNDECLARED])
    unused = sorted([
        pkg for pkg in package.get("dependencies", {})
        if pkg not in used and pkg not in ALLOWED_UNUSED_RUNTIME
    ])

    if missing:
        print("Missing dependencies detected:")
        for pkg in missing:
            print(f"  - {pkg}")

    if unused:
        print("Unused runtime dependencies detected:")
        for pkg in unused:
            print(f"  - {pkg}")

    if missing or unused:
        return 1

    print("Dashboard dependency consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
