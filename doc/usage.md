# MCP Diagram Server - Usage Guide

## Overview

The `mcp_diagram_server.py` now **fully supports MCP protocol** natively, without needing the wrapper. It can run in both HTTP mode and MCP stdio mode.

## Modes of Operation

### 1. HTTP Mode (Default)

Run as a FastAPI HTTP server:

```bash
# Using uvicorn directly
uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050

# Or using Python
python mcp_diagram_server.py --http --port 8050
```

**API Endpoints:**
- `POST /list_tools` - List available tools
- `POST /call_tool` - Execute a tool

**Use Case:** REST API for integration with other services

### 2. MCP Mode (stdio)

Run as an MCP-compliant stdio server:

```bash
python mcp_diagram_server.py --mcp
```

**MCP Methods:**
- `initialize` - Protocol handshake
- `tools/list` - List available tools
- `tools/call` - Execute a tool
- `ping` - Keepalive

**Use Case:** Direct integration with Cursor IDE or other MCP clients

## Cursor Configuration

### Option 1: Direct MCP Integration (Recommended)

Configure in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-diagram-server": {
      "command": "python3",
      "args": [
        "/absolute/path/to/mcp_diagram_server.py",
        "--mcp"
      ],
      "env": {}
    }
  }
}
```

**Important:** Replace `/absolute/path/to/` with the actual absolute path to your `mcp_diagram_server.py` file.

Then restart Cursor.

### Option 2: Using Poetry (With Virtual Environment)

If using Poetry for dependency management:

```json
{
  "mcpServers": {
    "mcp-diagram-server": {
      "command": "poetry",
      "args": [
        "run",
        "python",
        "/absolute/path/to/mcp_diagram_server.py",
        "--mcp"
      ],
      "env": {}
    }
  }
}
```

### Option 3: Hybrid Setup (Both MCP and HTTP)

You can run both simultaneously:

**Terminal 1: HTTP Server**
```bash
uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050
```

**Terminal 2: MCP Server** (for Cursor)
```bash
python mcp_diagram_server.py --mcp
```

Or configure Cursor to use the MCP mode directly (no need for HTTP server).

## Testing

### Test MCP Mode

```bash
python3 test_mcp_direct.py
```

This tests:
- ✅ Initialize handshake
- ✅ Tools listing
- ✅ Ping/pong

### Test HTTP Mode

```bash
# Start server
python mcp_diagram_server.py --http &

# Test
curl -X POST http://localhost:8050/list_tools
```

## Features

### Fully MCP-Compliant

- ✅ JSON-RPC 2.0 protocol
- ✅ Proper initialize handshake
- ✅ Standard error codes (-32700, -32601, -32602, -32603)
- ✅ Request/response ID tracking
- ✅ Ping/pong keepalive
- ✅ Notification handling
- ✅ Proper tool schemas

### Three Diagram Rendering Tools

1. **plantuml.render** - Renders PlantUML to SVG/PNG
2. **graphviz.render** - Renders Graphviz DOT to SVG/PNG
3. **mermaid.render** - Renders Mermaid to SVG/PNG

## Advantages

1. **Single File** - Everything in `mcp_diagram_server.py`
2. **No Wrapper Needed** - Native MCP implementation built-in
3. **Multiple Modes** - HTTP REST, MCP stdio, or SSE
4. **Simple Configuration** - Just point to one Python file
5. **Fully MCP-Compliant** - Passes all MCP protocol tests

