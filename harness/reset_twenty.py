#!/usr/bin/env python3
"""Reset the Twenty CRM state before a v2 trial.

The MCP API is tried first. Twenty soft deletes, so if the records are still
visible to find_many_* afterwards, the script falls back to the hard SQL reset.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from twenty_mcp import MCPClient, _read_dotenv, get_credentials

DB_URL_KEYS = ("TWENTY_DB_URL", "DATABASE_URL", "PG_DATABASE_URL")


def get_db_url(repo: Path | None) -> str | None:
    dotenv = _read_dotenv(repo)
    for key in DB_URL_KEYS:
        value = os.environ.get(key) or dotenv.get(key)
        if value:
            return value
    return None


def reset_sql(repo: Path | None, db_url: str | None = None) -> int:
    url = db_url or get_db_url(repo)
    if not url:
        print(
            "No Postgres URL found. Set TWENTY_DB_URL, DATABASE_URL or "
            "PG_DATABASE_URL, or pass --db-url."
        )
        return 1
    psql = shutil.which("psql")
    if not psql:
        print("psql not found on PATH; cannot run the hard SQL reset.")
        return 1
    sql_file = Path(__file__).with_name("reset_twenty.sql")
    print("Running hard SQL reset...")
    result = subprocess.run(
        [psql, url, "-v", "ON_ERROR_STOP=1", "-f", str(sql_file)]
    )
    return result.returncode


def reset(
    repo: Path | None,
    url: str | None,
    token: str | None,
    db_url: str | None = None,
) -> int:
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
        print("MCP reset left records:", dirty)
        if reset_sql(repo, db_url) != 0:
            print("Hard SQL reset failed or no database URL is configured.")
            return 1
        after = client.clean_counts()
        print("after SQL reset:", after)
        dirty = {k: v for k, v in after.items() if v != 0}
        if dirty:
            print("WARNING: records remain after SQL reset:", dirty)
            print("Restart Twenty if it caches records, then rerun.")
            return 1
    print("OK: clean state.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--url", default=None)
    parser.add_argument("--token", default=None)
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()
    raise SystemExit(
        reset(args.repo, args.url, args.token, args.db_url)
    )


if __name__ == "__main__":
    main()
