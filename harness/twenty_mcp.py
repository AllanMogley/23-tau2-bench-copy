#!/usr/bin/env python3
"""Small Twenty CRM MCP client used by the v2 harness scripts.

Credentials are read from environment variables first, then from a .env file
in the tau2 repo root:

    TWENTY_MCP_URL=http://host:3000/mcp?mode=direct
    TWENTY_MCP_TOKEN=...
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import requests


def _read_dotenv(repo: Optional[Path]) -> dict[str, str]:
    values: dict[str, str] = {}
    candidates = []
    if repo is not None:
        candidates.append(repo / ".env")
    candidates.append(Path.cwd() / ".env")
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        break
    return values


def get_credentials(
    repo: Optional[Path] = None,
    url: Optional[str] = None,
    token: Optional[str] = None,
) -> tuple[str, str]:
    dotenv = _read_dotenv(repo)
    mcp_url = url or os.environ.get("TWENTY_MCP_URL") or dotenv.get("TWENTY_MCP_URL")
    mcp_token = (
        token
        or os.environ.get("TWENTY_MCP_TOKEN")
        or dotenv.get("TWENTY_MCP_TOKEN")
    )
    if not mcp_url or not mcp_token:
        raise SystemExit(
            "Missing MCP credentials. Set TWENTY_MCP_URL and TWENTY_MCP_TOKEN, "
            "or create a .env file in the tau2 repo root."
        )
    return mcp_url, mcp_token


def extract_records(response: Any) -> list[dict]:
    seen: set[int] = set()
    preferred = (
        "result",
        "records",
        "data",
        "items",
        "results",
        "list",
        "nodes",
        "edges",
        "people",
        "companies",
        "opportunities",
        "tasks",
    )
    skip = {"content", "jsonrpc", "error", "success", "message", "id"}

    def walk(value: Any) -> list[dict]:
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                return []
            seen.add(id(value))
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if not isinstance(value, dict):
            return []
        for key in preferred:
            if key in value:
                found = walk(value[key])
                if found:
                    return found
        for key, item in value.items():
            if key in skip:
                continue
            found = walk(item)
            if found:
                return found
        return []

    return walk(response)


class MCPClient:
    def __init__(self, url: str, token: str, timeout: int = 60) -> None:
        self.url = url
        self.token = token
        self.timeout = timeout

    def call(self, tool_name: str, arguments: Optional[dict] = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "execute_tool",
                "arguments": {
                    "toolName": tool_name,
                    "arguments": arguments or {},
                },
            },
            "id": 1,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self.url, json=payload, headers=headers, timeout=self.timeout
        )
        response.raise_for_status()
        body = response.json()
        if "result" in body and "content" in body["result"]:
            text = body["result"]["content"][0].get("text", "{}")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
        return body

    def find_all(self, object_name: str, limit: int = 200) -> list[dict]:
        try:
            return extract_records(
                self.call(f"find_many_{object_name}", {"limit": limit})
            )
        except Exception:
            return []

    def delete_one(self, object_name: str, record_id: str) -> None:
        self.call(f"delete_one_{object_name}", {"id": record_id})

    def reset(self) -> dict[str, int]:
        """Delete tasks, opportunities, people and companies. Returns counts."""
        counts: dict[str, int] = {}
        for object_name in ("tasks", "opportunities", "people", "companies"):
            records = self.find_all(object_name)
            deleted = 0
            for record in records:
                record_id = record.get("id")
                if not record_id:
                    continue
                try:
                    self.delete_one(object_name, record_id)
                    deleted += 1
                except Exception:
                    pass
            counts[object_name] = deleted
        return counts

    def clean_counts(self) -> dict[str, int]:
        return {
            object_name: len(self.find_all(object_name))
            for object_name in ("tasks", "opportunities", "people", "companies")
        }

    def create_company(self, name: str) -> str:
        result = self.call(
            "create_one_company",
            {"name": name, "position": "last"},
        )
        return _created_id(result, "company", name)

    def create_person(
        self,
        first_name: str,
        last_name: str,
        company_id: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> str:
        args: dict[str, Any] = {
            "name": {"firstName": first_name, "lastName": last_name},
            "position": "last",
        }
        if company_id:
            args["companyId"] = company_id
        if job_title:
            args["jobTitle"] = job_title
        result = self.call("create_one_person", args)
        return _created_id(result, "person", f"{first_name} {last_name}")

    def create_opportunity(
        self,
        name: str,
        person_id: str,
        company_id: Optional[str] = None,
        stage: str = "NEW",
    ) -> str:
        args: dict[str, Any] = {
            "name": name,
            "stage": stage,
            "pointOfContactId": person_id,
            "position": "last",
        }
        if company_id:
            args["companyId"] = company_id
        result = self.call("create_one_opportunity", args)
        return _created_id(result, "opportunity", name)

    def create_task(self, title: str, status: str = "TODO") -> str:
        result = self.call(
            "create_one_task",
            {"title": title, "status": status, "position": "last"},
        )
        return _created_id(result, "task", title)


def _created_id(result: dict, object_name: str, label: str) -> str:
    if isinstance(result, dict) and result.get("success") and result.get("result"):
        record_id = result["result"].get("id")
        if record_id:
            return record_id
    raise RuntimeError(f"Failed to create {object_name} {label!r}: {result}")
