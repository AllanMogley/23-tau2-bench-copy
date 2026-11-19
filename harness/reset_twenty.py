#!/usr/bin/env python3
"""Reset the Twenty CRM state before a v2 trial.

Default mode uses the MCP API (soft delete) and then verifies that the
find_many_* calls return zero records. If the server keeps returning soft-deleted
records, use the SQL reset documented in README.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from twenty_mcp import MCPClient, get_credentials


def reset(repo: Path | None, url: str | None, token: str | None) -> int:
    mcp_url, mcp_token = get_credentials(repo, url, token)
    client = MCPClient(mcp_url, mcp_token)

    before = client.clean_counts()
    deleted = client.reset()
    after = client.clean_counts()

    print("before:", before)
    print("deleted:", deleted)
    print("after:", after)

    dirty = {k: v for k, v in after.items() if v != 0}
    if dirty:
        print("WARNING: these objects still have records after reset:", dirty)
        print("Use the SQL reset in harness/README.md and rerun the trial.")
        return 1
    print("OK: clean state.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--url", default=None)
    parser.add_argument("--token", default=None)
    args = parser.parse_args()
    raise SystemExit(reset(args.repo, args.url, args.token))


if __name__ == "__main__":
    main()
