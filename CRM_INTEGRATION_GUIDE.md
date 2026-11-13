# CRM Domain - Twenty CRM MCP Integration Guide

## Architecture Overview

The CRM domain in tau2-bench connects directly to Twenty CRM's MCP server.

```
┌─────────────────┐
│   tau2-bench    │
│     CRM Domain  │
│  (Your Code)    │
└────────┬────────┘
         │
         │ MCP Protocol
         │
         ▼
┌─────────────────┐
│ Twenty CRM MCP  │
│  Port 3000      │
│  /mcp?mode=direct
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Twenty CRM DB  │
│  PostgreSQL     │
│  Port 5432      │
└─────────────────┘
```

## Credentials Configuration

### Location

Credentials are stored in the project-level `.env` file at:
```
tau2-bench-copy/.env
```

### File Contents

```env
# Twenty CRM MCP Configuration
TWENTY_MCP_URL=http://x1000c0s4b0n0:3000/mcp?mode=direct
TWENTY_MCP_TOKEN=your_jwt_token_here

# Agent LLM Configuration (for CRM domain agent)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Optional voice configuration
ELEVENLABS_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### How Credentials Are Loaded

The `CRMMCPTools` class automatically reads from `tau2-bench-copy/.env`:

1. `CRMMCPTools.__init__()` is called when environment is created
2. `_load_mcp_credentials()` navigates to parent directory
3. Reads `.env` file and extracts `TWENTY_MCP_URL` and `TWENTY_MCP_TOKEN`
4. Credentials are stored in instance variables for MCP calls

## MCP Connection Details

### Connection Endpoint
- **URL**: `http://x1000c0s4b0n0:3000/mcp?mode=direct`
- **Protocol**: MCP v1.0 (protocolVersion `2025-06-18`)
- **Authentication**: Bearer token

## Tool Execution

### 1. Tool Call Flow

```python
# In CRMMCPTools class
def create_person(self, first_name, last_name, ...):
    # Step 1: Call Twenty CRM MCP
    mcp_result = self._call_mcp("create_one_person", {
        "name": {"firstName": first_name, "lastName": last_name},
        ...
    })
    
    # Step 2: Extract person ID from MCP response
    person_id = mcp_result["result"]["id"]
    
    # Step 3: Create local record with MCP data
    person = Person(id=person_id, ...)
    self.db.people[person_id] = person
    
    return person
```

### 2. Environment Setup

The `get_environment()` function in `environment.py`:
```python
def get_environment(db=None, solo_mode=False):
    if db is None:
        db = CRMDB.load(CRM_DB_PATH)
    
    # CRMMCPTools loads credentials from tau2-bench-copy/.env
    tools = CRMMCPTools(db)
    
    return Environment(
        domain_name="crm",
        policy=policy,
        tools=tools,
    )
```

## Key Features

### Trust-Tracking Tools
- `update_person_trust_commitment()` - Update relationship metrics
- `get_relationship_metrics()` - Analyze relationship health
- `update_person_lead_score()` - Update sales readiness

### MCP Integration
- Automatic credential loading from `tau2-bench-copy/.env`
- Error handling with graceful fallback
- JSON response parsing from nested MCP format
- Connection to Twenty CRM's 280+ tools

## Testing

### Verify MCP Connection

The domain tests MCP connectivity automatically when tools are called. To manually test:

```python
from tau2.domains.crm.tools import CRMMCPTools
from tau2.domains.crm.data_model import CRMDB

db = CRMDB.load("data/tau2/domains/crm/db.json")
tools = CRMMCPTools(db)

# This will fail gracefully if MCP is unavailable
try:
    result = tools._call_mcp("get_tool_catalog", {})
    print("MCP connection successful")
except Exception as e:
    print(f"MCP connection failed: {e}")
```

### Run Domain

```bash
# Test with verbose logs
tau2 run --domain crm --verbose-logs --num-tasks 1

# Check Twenty CRM Web UI for created records
```

## Troubleshooting

### "TWENTY_MCP_TOKEN not found" Error

**Solution**: Create `.env` file in `tau2-bench-copy/`:

```bash
cd /workspace/crm-environment/tau2-bench-copy
cat > .env << EOF
TWENTY_MCP_URL=http://x1000c0s4b0n0:3000/mcp?mode=direct
TWENTY_MCP_TOKEN=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImViNWUyMDUxLWFlYmYtNDU0NC04ODQyLTMxOWI0NzczZTdlMCJ9.eyJzdWIiOiJjYzNlODFmOC05YmQzLTQ0Y2QtYmMzOS01YTQ0ZTg3Y2ZkNTgiLCJ0eXBlIjoiQVBJX0tFWSIsIndvcmtzcGFjZUlkIjoiY2MzZTgxZjgtOWJkMy00NGNkLWJjMzktNWE0NGU4N2NmZDU4IiwiaWF0IjoxNzkyNjc3OTIyLCJleHAiOjQ5NDYyNzc5MjEsImp0aSI6IjE3NWZmZDk2LTVjYjctNDNhYy05MmNlLTAzNmQ2Yzk1ZTE5OCJ9.JAYa5Hd6YtIRqN5ziCnyIXNsS4dbMP2Fi3M_f8lsLJl4sEocmyhJ-h0XDmX9dN9scZ37tBE1xzHNlVoHwBeKFg
EOF
```

### MCP Connection Timeout

**Check**:
1. Network connectivity to `x1000c0s4b0n0:3000`
2. `.env` file has correct URL
3. MCP server is running on Twenty CRM

### Invalid Bearer Token

**Solution**:
1. Check token format: Should start with `eyJ...`
2. Verify token hasn't expired
3. Regenerate token from Twenty CRM if needed

## Files Modified

- ✅ `src/tau2/domains/crm/tools.py` - Added CRMMCPTools with MCP integration
- ✅ `.env` - Project-level credentials file
- ✅ `src/tau2/domains/crm/environment.py` - Uses CRMMCPTools

## Next Steps

1. ✅ Credentials in `tau2-bench-copy/.env` (project-level)
2. ✅ CRMMCPTools reads credentials automatically
3. Test domain execution with `tau2 run --domain crm`
4. Verify actions in Twenty CRM Web UI
5. Monitor trust/commitment metric updates
