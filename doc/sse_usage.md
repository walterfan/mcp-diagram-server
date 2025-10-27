# MCP SSE (Server-Sent Events) Mode

## Overview

The `mcp_diagram_server.py` now supports **three modes**:

1. **HTTP Mode** - REST API (legacy)
2. **MCP stdio Mode** - JSON-RPC over stdio
3. **MCP SSE Mode** - JSON-RPC over HTTP with Server-Sent Events ✨ **NEW**

## SSE Mode

### What is SSE?

Server-Sent Events (SSE) is a standard that allows a server to push data to a client over HTTP. In the context of MCP, it enables:
- Bidirectional JSON-RPC communication over HTTP
- Streaming responses
- Long-lived connections
- Better for web-based MCP clients

### How to Use

#### 1. Start the Server

```bash
# Start in HTTP mode (includes SSE endpoint)
uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050
```

#### 2. SSE Endpoint

The server exposes the `/sse` endpoint for MCP protocol:

```bash
POST http://localhost:8050/sse
```

#### 3. Send MCP Requests

All MCP methods work through the SSE endpoint:

**Initialize:**
```bash
curl -X POST http://localhost:8050/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

**List Tools:**
```bash
curl -X POST http://localhost:8050/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

**Call a Tool:**
```bash
curl -X POST http://localhost:8050/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "plantuml.render",
      "arguments": {
        "text": "@startuml\nAlice -> Bob\n@enduml",
        "format": "svg"
      }
    }
  }'
```

## Cursor Configuration (SSE Mode)

For Cursor, you can use SSE mode in two ways:

### Option 1: Using SSE Type

```json
{
  "mcpServers": {
    "mcp-diagram-server-sse": {
      "type": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

### Option 2: Command Line (stdio is still simpler)

For stdio mode (recommended for Cursor):
```json
{
  "mcpServers": {
    "mcp-diagram-server": {
      "command": "python3",
      "args": ["mcp_diagram_server.py", "--mcp"]
    }
  }
}
```

## When to Use SSE?

**Use SSE when:**
- ✅ Building a web-based MCP client
- ✅ Need streaming responses
- ✅ Want to integrate with existing HTTP infrastructure
- ✅ Testing from web browsers or Postman

**Use stdio when:**
- ✅ Using with Cursor IDE
- ✅ Want simplest setup
- ✅ Working locally
- ✅ Need best performance

## Example Python Client

```python
import requests
import json

SERVER = "http://localhost:8050/sse"

def call_mcp_tool(method, params=None, request_id=1):
    """Call an MCP method via SSE"""
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params:
        payload["params"] = params
    
    response = requests.post(SERVER, json=payload)
    return response.json()

# Initialize
response = call_mcp_tool("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
})
print("Init:", response)

# List tools
response = call_mcp_tool("tools/list", request_id=2)
print("Tools:", json.dumps(response, indent=2))

# Render diagram
response = call_mcp_tool("tools/call", {
    "name": "plantuml.render",
    "arguments": {
        "text": "@startuml\nAlice -> Bob\n@enduml",
        "format": "svg"
    }
}, request_id=3)
print("Diagram:", response.get("result", {}))
```

## Architecture

```
┌─────────────────┐
│  MCP Client     │
│  (Cursor/web)   │
└────────┬────────┘
         │ HTTP POST
         ↓
┌──────────────────────────────────┐
│  POST /sse                       │
│  mcp_diagram_server.py           │
│                                  │
│  - handle_sse_initialize()       │
│  - handle_sse_list_tools()      │
│  - handle_sse_call_tool()       │
│  - handle_sse_ping()            │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Rendering Functions             │
│  - render_plantuml()             │
│  - render_graphviz()             │
│  - render_mermaid()              │
└──────────────────────────────────┘
```

## Comparison

| Mode | Transport | Best For |
|------|-----------|----------|
| **HTTP** | REST API | Simple integrations |
| **stdio** | stdin/stdout | Cursor IDE, local development |
| **SSE** | HTTP + SSE | Web clients, streaming |

## Testing

```bash
# Start server
uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050

# Test SSE endpoint
curl -X POST http://localhost:8050/sse \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'

# Should return: {"jsonrpc":"2.0","id":1,"result":{}}
```

## Benefits of SSE Mode

1. **HTTP-based** - Works with standard HTTP libraries
2. **Web-friendly** - Can be used from browsers
3. **Standard MCP protocol** - JSON-RPC 2.0 compliant
4. **Flexible** - No special stdio handling needed
5. **Testable** - Easy to test with curl or Postman

## All Three Modes Work!

The server now supports:
- ✅ HTTP REST API (`/list_tools`, `/call_tool`)
- ✅ MCP stdio (`--mcp` flag)
- ✅ MCP SSE (`/sse` endpoint)

Choose the mode that best fits your use case!

