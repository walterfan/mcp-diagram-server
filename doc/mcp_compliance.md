# MCP Protocol Compliance

## Overview

The MCP diagram server is now **fully compliant** with the Model Context Protocol (MCP) specification.

## Architecture

```
┌─────────────────┐
│   Cursor IDE    │
└────────┬────────┘
         │ JSON-RPC 2.0 via stdio (--mcp mode)
         ↓
┌─────────────────────────────────────┐
│   mcp_diagram_server.py              │
│   (Fully MCP-Compliant)              │
│   - JSON-RPC 2.0                     │
│   - MCP Protocol Handlers            │
│   - Error Handling                   │
│   - HTTP API support                 │
│   - SSE mode support                 │
└────────┬──────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│   Rendering Functions               │
│   - PlantUML Server                  │
│   - Graphviz                         │
│   - Mermaid CLI                      │
└─────────────────────────────────────┘
```

## MCP Compliance Features

### ✅ Implemented

1. **JSON-RPC 2.0 Protocol**
   - Proper request/response structure
   - `id` field mapping
   - Error handling with standard codes

2. **Initialize Handshake**
   - Responds to `initialize` method
   - Provides `protocolVersion: "2024-11-05"`
   - Declares capabilities: `tools`, `prompts`, `resources`
   - Returns server info

3. **Tool Listing** (`tools/list`)
   - Returns tool schemas in MCP format
   - Includes `inputSchema` with JSON schema
   - Proper property type inference

4. **Tool Execution** (`tools/call`)
   - Accepts tool name and arguments
   - Returns content in MCP format
   - Supports text and image content types

5. **Ping/Pong Keepalive**
   - Responds to `ping` method
   - Maintains connection health

6. **Error Handling**
   - Standard JSON-RPC error codes:
     - `-32700`: Parse error
     - `-32601`: Method not found
     - `-32603`: Internal error
   - Includes error `id` field

7. **Notifications**
   - Handles `notifications/initialized`

## Usage

### Configuration

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-diagram-server": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp_diagram_server.py", "--mcp"],
      "env": {}
    }
  }
}
```

### Supported Tools

The server exposes three MCP tools:

1. **`plantuml.render`**
   - Arguments: `text` (string), `format` (string, optional)
   - Returns: SVG or PNG diagram

2. **`graphviz.render`**
   - Arguments: `dot` (string), `format` (string, optional)
   - Returns: SVG or PNG diagram

3. **`mermaid.render`**
   - Arguments: `text` (string), `format` (string, optional)
   - Returns: SVG or PNG diagram

## Testing

Run the MCP compliance test suite:

```bash
python3 test_mcp_compliance.py
```

This tests:
- Initialize handshake
- Tools listing
- Ping/pong
- Error handling

## MCP Protocol Features

### Request Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### Response Format

Success:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

Error:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

## Differences from Original

### Before (MCP-like)
- Basic JSON-RPC without proper error handling
- Missing `id` fields in responses
- No initialize handshake
- Limited error codes

### After (Fully MCP-Compliant)
- Complete JSON-RPC 2.0 implementation
- All responses include `id` field
- Proper initialize handshake
- Standard error codes
- Ping/pong support
- Proper notification handling

## Compliance Checklist

- [x] JSON-RPC 2.0 protocol
- [x] Initialize handshake
- [x] Protocol version negotiation
- [x] Capabilities declaration
- [x] Server info response
- [x] Tools listing with proper schema
- [x] Tool execution
- [x] Error handling with standard codes
- [x] Request ID tracking
- [x] Ping/pong keepalive
- [x] Notification handling
- [x] Content type handling (text/image)
- [x] Base64 encoding for binary data

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

