#!/usr/bin/env python3
"""Unit tests for the learn-claude-code repository structure."""

import os
import sys

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")

EXPECTED_SESSIONS = [
    "s01", "s02", "s03", "s04", "s05", "s06",
    "s07", "s08", "s09", "s10", "s11", "s12",
]
EXPECTED_LOCALES = ["en", "zh", "ja", "el"]


def test_agent_files_exist():
    """All expected agent session files must exist."""
    missing = []
    for session in EXPECTED_SESSIONS:
        matches = [f for f in os.listdir(AGENTS_DIR) if f.startswith(session + "_") and f.endswith(".py")]
        if not matches:
            missing.append(session)
    assert not missing, f"Missing agent files for sessions: {missing}"
    print(f"  ✓ All {len(EXPECTED_SESSIONS)} agent files found")


def test_docs_exist_for_all_locales():
    """Each locale must have a doc file for every session."""
    for locale in EXPECTED_LOCALES:
        locale_dir = os.path.join(DOCS_DIR, locale)
        assert os.path.isdir(locale_dir), f"Missing locale directory: docs/{locale}"
        for session in EXPECTED_SESSIONS:
            matches = [f for f in os.listdir(locale_dir) if f.startswith(session + "-") and f.endswith(".md")]
            assert matches, f"Missing doc for {locale}/{session}"
    print(f"  ✓ Docs exist for all {len(EXPECTED_SESSIONS)} sessions × {len(EXPECTED_LOCALES)} locales")


def test_web_package_json_exists():
    """The web/package.json must exist for the GitHub Pages build."""
    pkg = os.path.join(REPO_ROOT, "web", "package.json")
    assert os.path.isfile(pkg), "web/package.json not found"
    print("  ✓ web/package.json found")


def test_next_config_has_output_export():
    """next.config.ts must be configured for static export (required for GitHub Pages)."""
    config = os.path.join(REPO_ROOT, "web", "next.config.ts")
    assert os.path.isfile(config), "web/next.config.ts not found"
    content = open(config).read()
    assert 'output: "export"' in content, "next.config.ts must have output: 'export' for GitHub Pages"
    assert "basePath" in content, "next.config.ts must configure basePath for GitHub Pages subpath"
    print("  ✓ next.config.ts has output:export and basePath configured")


if __name__ == "__main__":
    tests = [
        test_agent_files_exist,
        test_docs_exist_for_all_locales,
        test_web_package_json_exists,
        test_next_config_has_output_export,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: unexpected error: {e}")
            failed += 1

    if failed:
        print(f"\n{failed}/{len(tests)} tests failed.")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} unit tests passed.")
