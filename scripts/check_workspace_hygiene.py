#!/usr/bin/env python3
"""
Workspace Hygiene & Root Isolation Validator
Enforces AGENTS.md Root & Sandbox Isolation rules:
- Keeps repository root clean (only root config files, README.md, AGENTS.md).
- Ensures experimental spikes stay inside prototypes/ and documentation in docs/ or openspec/.
- Zero external dependencies (Python 3.8+ standard library).
"""

import sys
from pathlib import Path

# Explicit allowed files in repository root
ALLOWED_ROOT_FILES = {
    "README.md",
    "README.en.md",
    "AGENTS.md",
    "USER_GUIDE.md",
    "main.py",
    "requirements.txt",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    ".editorconfig",
    ".git",
}

# Explicit allowed directories in repository root
ALLOWED_ROOT_DIRS = {
    ".git",
    ".github",
    ".agents",
    ".vscode",
    # Production payroll lives under backend/; keep the root allow-list explicit.
    "backend",
    "docs",
    "frontend",
    "openspec",
    "prototypes",
    "scripts",
    "tools",
}

# Directories and files ignored (e.g. local developer tools, IDEs, caches)
IGNORED_ROOT_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    ".idea",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "__pycache__",
}


def check_workspace_hygiene(repo_root: Path) -> int:
    violations = []

    for item in repo_root.iterdir():
        name = item.name

        # Skip local environments, virtualenvs, or IDE/tool cache directories
        if (
            name in IGNORED_ROOT_NAMES
            or name.startswith(".env")
            or name.startswith(".venv")
            or name.startswith("venv")
        ):
            continue

        # Handle symlinks explicitly to detect broken or dangling symlinks
        if item.is_symlink():
            if not item.exists():
                violations.append(
                    f"Broken symlink in repository root: '{name}'. "
                    f"Remove broken symlinks to preserve workspace hygiene."
                )
                continue

        if item.is_file():
            # Flag any root file not in the allowed whitelist
            if name not in ALLOWED_ROOT_FILES:
                violations.append(
                    f"Unauthorized root file: '{name}'. "
                    f"Move documentation to docs/ or openspec/, and scripts to scripts/ or prototypes/."
                )
        elif item.is_dir():
            # Flag any root folder not in the allowed whitelist
            if name not in ALLOWED_ROOT_DIRS:
                violations.append(
                    f"Unauthorized root directory: '{name}/'. "
                    f"Spikes must be placed in prototypes/<name>/ per AGENTS.md line 45."
                )
        else:
            violations.append(
                f"Unknown or invalid filesystem entry in repository root: '{name}'."
            )

    if violations:
        print("=" * 70, file=sys.stderr)
        print("❌ WORKSPACE HYGIENE VIOLATION DETECTED", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("AGENTS.md explicitly mandates Root & Sandbox Isolation:\n", file=sys.stderr)
        for v in violations:
            print(f"  • {v}", file=sys.stderr)
        print("\nReference: AGENTS.md line 43 ('Workspace Hygiene & Pre-Archive Gate')", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return 1

    print("✅ [OK] Workspace hygiene check passed. Root and sandbox isolation confirmed.")
    return 0


if __name__ == "__main__":
    root_path = Path(__file__).resolve().parent.parent
    sys.exit(check_workspace_hygiene(root_path))
