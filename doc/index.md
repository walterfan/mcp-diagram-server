# Documentation Index

## Quick Start
- **[usage.md](./usage.md)** - Complete guide to using the MCP diagram server
- **[cursor_direct_usage.md](./cursor_direct_usage.md)** - Using MCP tools directly in Cursor (no scripts needed!)
- **[web_ui_usage.md](./web_ui_usage.md)** - Web UI for interactive diagram rendering

## Transport Modes
- **[sse_usage.md](./sse_usage.md)** - Server-Sent Events (SSE) mode guide

## MCP Protocol
- **[mcp_compliance.md](./mcp_compliance.md)** - MCP protocol compliance details and architecture

## Getting Started

1. **Start with [usage.md](./usage.md)** - Learn how to run the server in different modes
2. **Configure Cursor** - Use [cursor_direct_usage.md](./cursor_direct_usage.md) to set up Cursor integration
3. **Understand the Protocol** - Read [mcp_compliance.md](./mcp_compliance.md) for MCP details
4. **Try the Web UI** - Check out [web_ui_usage.md](./web_ui_usage.md) for interactive rendering

## Feature Overview

This MCP diagram server supports three transport modes:
- **HTTP REST API** - Traditional REST endpoints
- **MCP stdio** - Native MCP protocol for Cursor IDE
- **MCP SSE** - Server-Sent Events for web clients

All three modes support the same three diagram rendering tools:
1. PlantUML
2. Graphviz (DOT)
3. Mermaid

