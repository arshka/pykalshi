#!/usr/bin/env python
"""Generate synchronous API from async source files.

Usage:
    python scripts/generate_sync.py [--write|--check]

Default mode is --write.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASYNC_DIR = REPO_ROOT / "pykalshi" / "_async"
SYNC_DIR = REPO_ROOT / "pykalshi" / "_sync"

GENERATED_MODULES = [
    "client.py",
    "portfolio.py",
    "orders.py",
    "markets.py",
    "events.py",
    "exchange.py",
    "api_keys.py",
    "communications.py",
    "mve.py",
]

# Class renames: AsyncX -> X (applied with word boundaries)
CLASS_RENAMES = {
    "AsyncKalshiClient": "KalshiClient",
    "AsyncPortfolio": "Portfolio",
    "AsyncOrder": "Order",
    "AsyncMarket": "Market",
    "AsyncSeries": "Series",
    "AsyncEvent": "Event",
    "AsyncExchange": "Exchange",
    "AsyncAPIKeys": "APIKeys",
    "AsyncCommunications": "Communications",
    "AsyncMveCollection": "MveCollection",
    "AsyncRateLimiterProtocol": "RateLimiterProtocol",
    "AsyncFeed": "Feed",
}

HEADER = (
    "# AUTO-GENERATED from pykalshi/_async/{filename} — do not edit manually.\n"
    "# Re-run: python scripts/generate_sync.py\n"
)


def transform(source: str, filename: str) -> str:
    """Apply all sync transforms to async source code."""
    lines = source.split("\n")
    result_lines = []

    for line in lines:
        # Remove # type: ignore[override]
        line = re.sub(r"\s*#\s*type:\s*ignore\[override\]", "", line)

        # Keyword transforms
        line = re.sub(r"\basync\s+def\b", "def", line)
        line = re.sub(r"\basync\s+with\b", "with", line)
        line = re.sub(r"\basync\s+for\b", "for", line)
        line = re.sub(r"\bawait\s+", "", line)

        # stdlib swaps
        line = re.sub(r"\basyncio\.sleep\b", "time.sleep", line)

        # httpx swaps
        line = re.sub(r"\bhttpx\.AsyncClient\b", "httpx.Client", line)

        # Protocol method renames
        line = re.sub(r"\b__aenter__\b", "__enter__", line)
        line = re.sub(r"\b__aexit__\b", "__exit__", line)
        line = re.sub(r"\baclose\b", "close", line)

        # Special-case import (must come BEFORE class renames)
        line = re.sub(
            r"from \.\.afeed import AsyncFeed", "from ..feed import Feed", line
        )

        # Class renames
        for async_name, sync_name in CLASS_RENAMES.items():
            line = re.sub(rf"\b{async_name}\b", sync_name, line)

        # import asyncio -> import time
        if re.match(r"^import asyncio\s*$", line):
            line = "import time"

        result_lines.append(line)

    result = "\n".join(result_lines)

    # Deduplicate consecutive 'import time' lines
    result = re.sub(
        r"^(import time\n)(?=import time\n)", "", result, flags=re.MULTILINE
    )

    # Add header
    header = HEADER.format(filename=filename)
    result = header + result

    return result


def validate_allowlist() -> bool:
    """Check that no unexpected .py files exist in _async/."""
    if not ASYNC_DIR.exists():
        return True

    async_files = {f.name for f in ASYNC_DIR.glob("*.py") if f.name != "__init__.py"}
    allowed = set(GENERATED_MODULES)
    unexpected = async_files - allowed

    if unexpected:
        print(f"ERROR: Unexpected files in _async/: {unexpected}", file=sys.stderr)
        print(
            "Add them to GENERATED_MODULES in scripts/generate_sync.py", file=sys.stderr
        )
        return False
    return True


def main() -> int:
    mode = "--write"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if mode not in ("--write", "--check"):
        print(f"Usage: {sys.argv[0]} [--write|--check]", file=sys.stderr)
        return 1

    if not validate_allowlist():
        return 1

    # Determine which modules exist in _async/
    present = []
    for module in GENERATED_MODULES:
        src = ASYNC_DIR / module
        if src.exists():
            present.append(module)
        else:
            print(f"skipped: {module} (not yet migrated)")

    if not present:
        print("No async modules found to generate.")
        return 0

    errors = []

    for module in present:
        src = ASYNC_DIR / module
        source = src.read_text()
        generated = transform(source, module)
        dest = SYNC_DIR / module

        if mode == "--write":
            SYNC_DIR.mkdir(parents=True, exist_ok=True)
            dest.write_text(generated)
            print(f"wrote: _sync/{module}")
        else:  # --check
            if not dest.exists():
                errors.append(
                    f"_sync/{module} does not exist (expected from _async/{module})"
                )
                continue
            existing = dest.read_text()
            if existing != generated:
                errors.append(f"_sync/{module} is out of date")

    # Check for stale files in _sync/
    if mode == "--check" and SYNC_DIR.exists():
        sync_files = {f.name for f in SYNC_DIR.glob("*.py") if f.name != "__init__.py"}
        expected = set(present)
        stale = sync_files - expected
        for s in stale:
            errors.append(f"_sync/{s} is stale (no corresponding _async/ source)")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if mode == "--check":
        print("OK: _sync/ is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
