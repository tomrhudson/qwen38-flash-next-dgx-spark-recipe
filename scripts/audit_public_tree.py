#!/usr/bin/env python3
"""Fail if the public repository contains likely secrets, weights, or topology."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_ENV_FILES = {".env.example"}
WEIGHT_SUFFIXES = {
    ".safetensors", ".gguf", ".ckpt", ".pt", ".pth", ".onnx"
}

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

# Split deployment-local markers so the audit source does not match itself.
PRIVATE_TOPOLOGY_PATTERNS = {
    "private host label": re.compile(
        r"\b(?:atlan" + r"tis|colum" + r"bia|base" + r"star)\b", re.IGNORECASE
    ),
    "private LAN prefix": re.compile(r"\b192\." + r"168\.90\."),
    "tailnet address": re.compile(r"\b100\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}\b"),
}


def repository_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(
            path for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def main() -> int:
    failures: list[str] = []
    files = repository_files()
    for path in files:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            failures.append(f"symlink is not allowed: {relative}")
            continue
        if path.name.startswith(".env") and path.name not in ALLOWED_ENV_FILES:
            failures.append(f"unapproved environment file: {relative}")
        if path.suffix.lower() in WEIGHT_SUFFIXES or re.fullmatch(
            r"(?:pytorch_)?model.*\.bin", path.name, re.IGNORECASE
        ):
            failures.append(f"model-weight artifact: {relative}")
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            failures.append(f"file exceeds 5 MiB: {relative} ({size} bytes)")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"unexpected binary file: {relative}")
            continue
        for label, pattern in {**SECRET_PATTERNS, **PRIVATE_TOPOLOGY_PATTERNS}.items():
            if pattern.search(text):
                failures.append(f"{label} pattern: {relative}")

    if failures:
        print("PUBLIC_TREE_AUDIT_FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"PUBLIC_TREE_AUDIT_OK files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
