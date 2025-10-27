#!/usr/bin/env python3
"""
MCP stdio wrapper for the HTTP diagram server
Fully MCP-compliant implementation
"""
import json
import sys
import requests
import base64

SERVER = "http://localhost:8050"

def write_response(response: dict):
    """Write JSON response to stdout"""
    print(json.dumps(response))
    sys.stdout.flush()

def write_error(request_id, code: int, message: str, data=None):
    """Write standardized JSON-RPC error response"""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    
    write_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error
    })

def handle_initialize(request: dict):
    """Handle MCP initialize request"""
    request_id = request.get("id")
    
    # Check if client supports MCP protocol
    protocol_version = request.get("params", {}).get("protocolVersion", "unknown")
    
    write_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "prompts": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "mcp-diagram-server",
                "version": "0.1.0"
            }
        }
    })

def handle_initialized(request: dict):
    """Handle MCP initialized notification"""
    # This is a notification, no response needed
    pass

def list_tools(request_id):
    """List available tools with proper MCP schema"""
    try:
        resp = requests.post(f"{SERVER}/list_tools", timeout=5)
        data = resp.json()
        
        if data.get("ok"):
            tools = []
            for tool in data.get("tools", []):
                # Transform to MCP tool schema
                tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": _build_properties_from_tool(tool)
                    }
                })
            
            write_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools
                }
            })
        else:
            write_error(request_id, -32603, "Failed to list tools from server")
    except requests.RequestException as e:
        write_error(request_id, -32603, "Connection error", str(e))
    except Exception as e:
        write_error(request_id, -32603, "Internal error", str(e))

def _build_properties_from_tool(tool: dict) -> dict:
    """Build JSON schema properties from tool arguments description"""
    props = {}
    args = tool.get("arguments", {})
    
    for arg_name, arg_desc in args.items():
        # Infer type from argument description
        if "string" in str(arg_desc).lower():
            arg_type = "string"
        elif "int" in str(arg_desc).lower() or "number" in str(arg_desc).lower():
            arg_type = "number"
        elif "bool" in str(arg_desc).lower():
            arg_type = "boolean"
        else:
            arg_type = "string"
        
        props[arg_name] = {
            "type": arg_type,
            "description": str(arg_desc)
        }
    
    return props

def call_tool(request_id, name: str, arguments: dict):
    """Call a tool with proper error handling"""
    try:
        resp = requests.post(
            f"{SERVER}/call_tool",
            json={"name": name, "arguments": arguments},
            timeout=30
        )
        data = resp.json()
        
        if data.get("ok"):
            result = data["result"]
            
            write_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Diagram rendered successfully as {result.get('content_type', 'unknown')}"
                        },
                        {
                            "type": "image",
                            "mimeType": result.get("content_type", "image/png"),
                            "data": result.get("data_base64", "")
                        }
                    ]
                }
            })
        else:
            write_error(request_id, -32603, data.get("error", "Tool execution failed"))
    except requests.Timeout:
        write_error(request_id, -32603, "Request timeout")
    except requests.RequestException as e:
        write_error(request_id, -32603, "Connection error", str(e))
    except Exception as e:
        write_error(request_id, -32603, "Internal error", str(e))

def handle_ping(request_id):
    """Handle ping/pong keepalive"""
    write_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {}
    })

def main():
    """Main loop reading JSON-RPC requests from stdin"""
    for line in sys.stdin:
        if not line.strip():
            continue
            
        request = None
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # Handle initialization
            if method == "initialize":
                handle_initialize(request)
            elif method == "notifications/initialized":
                handle_initialized(request)
            # Handle tools
            elif method == "tools/list":
                list_tools(request_id)
            elif method == "tools/call":
                call_tool(
                    request_id,
                    params.get("name"),
                    params.get("arguments", {})
                )
            # Handle ping
            elif method == "ping":
                handle_ping(request_id)
            # Unknown method
            else:
                write_error(request_id, -32601, f"Method not found: {method}")
                
        except json.JSONDecodeError as e:
            write_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            })
        except Exception as e:
            write_error(
                request.get("id") if request else None,
                -32603,
                "Internal error",
                str(e)
            )

if __name__ == "__main__":
    main()