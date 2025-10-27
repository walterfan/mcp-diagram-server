"""
MCP Diagram Server - Fully MCP-Compliant
Supports HTTP REST API, MCP stdio, and MCP SSE (Server-Sent Events)

Usage:
    # HTTP mode (FastAPI)
    uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050
    
    # MCP mode (stdio)
    python mcp_diagram_server.py --mcp
    
    # HTTP with custom config
    python mcp_diagram_server.py --http --port 8050

API:
HTTP mode:
- POST /list_tools -> returns available tools and their schemas
- POST /call_tool -> { "name": "tool_name", "arguments": { ... } }

MCP SSE mode:
- GET /sse -> Server-Sent Events endpoint for MCP protocol
- POST /sse -> Accept JSON-RPC requests, stream responses

MCP stdio mode:
- Implements full MCP protocol via JSON-RPC 2.0 over stdio
- Supports: initialize, tools/list, tools/call, ping

"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import base64
import json
import zlib
import requests
import subprocess
import shutil
import tempfile
import os
import sys
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MCP Diagram Server")

# -------------------- Web UI Endpoint --------------------

@app.get("/")
async def root():
    """Serve the web UI"""
    return FileResponse("diagram_ui.html")

# -------------------- Utility: PlantUML encoder --------------------
# PlantUML server expects diagram text compressed (deflate) and encoded in a custom base64.
# Implementation adapted from PlantUML specs.

_ENCODE_TABLE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"

def _plantuml_encode(data: bytes) -> str:
    # custom base64 using 6-bit groups
    res = []
    bit_buf = 0
    bit_len = 0
    for b in data:
        bit_buf = (bit_buf << 8) | b
        bit_len += 8
        while bit_len >= 6:
            bit_len -= 6
            idx = (bit_buf >> bit_len) & 0x3F
            res.append(_ENCODE_TABLE[idx])
    if bit_len > 0:
        idx = (bit_buf << (6 - bit_len)) & 0x3F
        res.append(_ENCODE_TABLE[idx])
    return ''.join(res)


def plantuml_text_to_server_key(text: str) -> str:
    # deflate (zlib) but strip zlib header as PlantUML uses raw deflate
    compressed = zlib.compress(text.encode('utf-8'))
    # strip zlib header (first 2 bytes) and checksum (last 4 bytes)
    # alternative approach: use zlib.compressobj with -15 window to get raw deflate
    comp = zlib.compressobj(level=9, wbits=-15)
    raw = comp.compress(text.encode('utf-8')) + comp.flush()
    return _plantuml_encode(raw)

# -------------------- Rendering backends --------------------

def render_plantuml(text: str, format: str = "svg") -> bytes:
    """Render using public PlantUML server as fallback.
    format: 'svg' or 'png'
    Returns raw bytes of image/svg+xml or PNG.
    """
    key = plantuml_text_to_server_key(text)
    server = os.environ.get('PLANTUML_SERVER', 'https://www.plantuml.com/plantuml')
    url = f"{server}/{format}/{key}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.content


def render_graphviz(dot_src: str, format: str = 'png') -> bytes:
    """Render Graphviz using graphviz package or dot binary.
    format: 'png' or 'svg'.
    """
    try:
        # Prefer python-graphviz if available
        from graphviz import Source
        src = Source(dot_src)
        out = src.pipe(format=format)
        return out
    except Exception:
        # fallback to dot binary
        dot_bin = shutil.which('dot')
        if not dot_bin:
            raise RuntimeError('graphviz not available: install python-graphviz or dot binary')
        p = subprocess.Popen([dot_bin, f'-T{format}'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(dot_src.encode('utf-8'))
        if p.returncode != 0:
            raise RuntimeError(f'dot failed: {err.decode()}')
        return out


def render_mermaid(mmd_text: str, format: str = 'png') -> bytes:
    """Render mermaid using mermaid-cli (mmdc). Requires node/npm and @mermaid-js/mermaid-cli available.
    We try to run `mmdc` via npx if installed locally.
    """
    # Find mmdc: try local binary, then npx
    mmdc_bin = shutil.which('mmdc')
    use_npx = False
    if not mmdc_bin:
        # prefer npx fallback
        npx_bin = shutil.which('npx')
        if npx_bin:
            mmdc_bin = npx_bin
            use_npx = True
        else:
            raise RuntimeError('mermaid-cli (mmdc) not found; install with `npm i -g @mermaid-js/mermaid-cli` or ensure npx is available')

    with tempfile.TemporaryDirectory() as td:
        in_file = os.path.join(td, 'diagram.mmd')
        out_file = os.path.join(td, f'out.{format}')
        with open(in_file, 'w', encoding='utf-8') as f:
            f.write(mmd_text)
        if use_npx:
            cmd = [mmdc_bin, '@mermaid-js/mermaid-cli', '-i', in_file, '-o', out_file, '-t', 'default']
        else:
            cmd = [mmdc_bin, '-i', in_file, '-o', out_file, '-t', 'default']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError(f'mmdc failed: {err.decode()}')
        with open(out_file, 'rb') as f:
            return f.read()

# -------------------- MCP-like server implementation --------------------

class CallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


@app.post('/list_tools')
async def list_tools():
    tools = get_tools_list()
    return {'ok': True, 'tools': tools}


@app.post('/call_tool')
async def call_tool(req: CallRequest):
    try:
        if req.name == 'plantuml.render':
            text = req.arguments.get('text')
            if not text:
                raise HTTPException(status_code=400, detail='text is required')
            fmt = req.arguments.get('format', 'svg')
            data = render_plantuml(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            return {'ok': True, 'result': {'content_type': ctype, 'data_base64': base64.b64encode(data).decode('ascii')}}

        elif req.name == 'graphviz.render':
            text = req.arguments.get('text')
            if not text:
                raise HTTPException(status_code=400, detail='text is required')
            fmt = req.arguments.get('format', 'png')
            data = render_graphviz(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            return {'ok': True, 'result': {'content_type': ctype, 'data_base64': base64.b64encode(data).decode('ascii')}}

        elif req.name == 'mermaid.render':
            text = req.arguments.get('text')
            if not text:
                raise HTTPException(status_code=400, detail='text is required')
            fmt = req.arguments.get('format', 'png')
            data = render_mermaid(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            return {'ok': True, 'result': {'content_type': ctype, 'data_base64': base64.b64encode(data).decode('ascii')}}

        else:
            raise HTTPException(status_code=404, detail='tool not found')
    except HTTPException:
        raise
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# -------------------- MCP SSE (Server-Sent Events) Endpoints --------------------

@app.post('/sse')
async def mcp_sse_endpoint(request: Request):
    """
    MCP SSE endpoint for handling JSON-RPC requests via Server-Sent Events
    Accepts HTTP POST with JSON-RPC payload, streams responses as SSE
    """
    try:
        body = await request.json()
        request_data = body
        
        # Handle the MCP request
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        response = None
        
        if method == "initialize":
            response = handle_sse_initialize(request_id)
        elif method == "notifications/initialized":
            response = None  # Notification, no response
        elif method == "tools/list":
            response = handle_sse_list_tools(request_id)
        elif method == "tools/call":
            response = handle_sse_call_tool(
                request_id,
                params.get("name"),
                params.get("arguments", {})
            )
        elif method == "ping":
            response = handle_sse_ping(request_id)
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # Return as JSON (SSE format would stream, but for simplicity we return JSON)
        return response if response else {"status": "ok"}
        
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id") if 'request' in locals() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }

def handle_sse_initialize(request_id):
    """Handle SSE initialize request"""
    return {
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
    }

def handle_sse_list_tools(request_id):
    """Handle SSE tools/list request"""
    tools_list = get_tools_list()
    mcp_tools = []
    
    for tool in tools_list:
        mcp_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": {
                "type": "object",
                "properties": build_tool_schema(tool)
            }
        })
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": mcp_tools
        }
    }

def handle_sse_call_tool(request_id, name: str, arguments: dict):
    """Handle SSE tools/call request"""
    try:
        # Use existing rendering functions
        if name == 'plantuml.render':
            text = arguments.get('text')
            if not text:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "text is required for plantuml.render"}
                }
            fmt = arguments.get('format', 'svg')
            data = render_plantuml(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            
        elif name == 'graphviz.render':
            text = arguments.get('text')
            if not text:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "text is required for graphviz.render"}
                }
            fmt = arguments.get('format', 'png')
            data = render_graphviz(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            
        elif name == 'mermaid.render':
            text = arguments.get('text')
            if not text:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "text is required for mermaid.render"}
                }
            fmt = arguments.get('format', 'png')
            data = render_mermaid(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"}
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Diagram rendered successfully as {ctype}"
                    },
                    {
                        "type": "image",
                        "mimeType": ctype,
                        "data": base64.b64encode(data).decode('ascii')
                    }
                ]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": "Tool execution failed",
                "data": str(e)
            }
        }

def handle_sse_ping(request_id):
    """Handle SSE ping request"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {}
    }


# -------------------- MCP Protocol Implementation --------------------

def get_tools_list():
    """Get list of available tools"""
    return [
        {
            'name': 'plantuml.render',
            'description': 'Render PlantUML diagram text to image',
            'arguments': {
                'text': 'string (PlantUML script)',
                'format': "string, 'svg' or 'png' (optional, default 'svg')",
            }
        },
        {
            'name': 'graphviz.render',
            'description': 'Render Graphviz DOT source to image',
            'arguments': {
                'text': 'string (Graphviz DOT source)',
                'format': "string, 'png' or 'svg' (optional, default 'png')",
            }
        },
        {
            'name': 'mermaid.render',
            'description': 'Render Mermaid diagram to image',
            'arguments': {
                'text': 'string (Mermaid source)',
                'format': "string, 'png' or 'svg' (optional, default 'png')",
            }
        }
    ]

def build_tool_schema(tool):
    """Build JSON schema for a tool from its arguments"""
    props = {}
    args = tool.get('arguments', {})
    
    for arg_name, arg_desc in args.items():
        # Infer type from description
        desc_str = str(arg_desc).lower()
        if 'string' in desc_str or arg_name == 'format':
            arg_type = 'string'
        elif 'int' in desc_str or 'number' in desc_str:
            arg_type = 'number'
        elif 'bool' in desc_str:
            arg_type = 'boolean'
        else:
            arg_type = 'string'
        
        props[arg_name] = {
            'type': arg_type,
            'description': str(arg_desc)
        }
    
    return props

def write_mcp_response(response: dict):
    """Write JSON response to stdout for MCP"""
    print(json.dumps(response))
    sys.stdout.flush()

def write_mcp_error(request_id, code: int, message: str, data=None):
    """Write standardized JSON-RPC error response"""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    
    write_mcp_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error
    })

def handle_mcp_initialize(request: dict):
    """Handle MCP initialize request"""
    request_id = request.get("id")
    
    write_mcp_response({
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

def handle_mcp_list_tools(request_id):
    """Handle MCP tools/list request"""
    tools_list = get_tools_list()
    mcp_tools = []
    
    for tool in tools_list:
        mcp_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": {
                "type": "object",
                "properties": build_tool_schema(tool)
            }
        })
    
    write_mcp_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": mcp_tools
        }
    })

def handle_mcp_call_tool(request_id, name: str, arguments: dict):
    """Handle MCP tools/call request"""
    try:
        # Use existing call_tool logic
        if name == 'plantuml.render':
            text = arguments.get('text')
            if not text:
                write_mcp_error(request_id, -32602, 'text is required for plantuml.render')
                return
            fmt = arguments.get('format', 'svg')
            data = render_plantuml(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            
        elif name == 'graphviz.render':
            text = arguments.get('text')
            if not text:
                write_mcp_error(request_id, -32602, 'text is required for graphviz.render')
                return
            fmt = arguments.get('format', 'png')
            data = render_graphviz(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
            
        elif name == 'mermaid.render':
            text = arguments.get('text')
            if not text:
                write_mcp_error(request_id, -32602, 'text is required for mermaid.render')
                return
            fmt = arguments.get('format', 'png')
            data = render_mermaid(text, format=fmt)
            ctype = 'image/svg+xml' if fmt == 'svg' else 'image/png'
        else:
            write_mcp_error(request_id, -32601, f"Unknown tool: {name}")
            return
        
        # Return MCP-formatted response
        write_mcp_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Diagram rendered successfully as {ctype}"
                    },
                    {
                        "type": "image",
                        "mimeType": ctype,
                        "data": base64.b64encode(data).decode('ascii')
                    }
                ]
            }
        })
    except Exception as e:
        write_mcp_error(request_id, -32603, "Tool execution failed", str(e))

def handle_mcp_ping(request_id):
    """Handle MCP ping request"""
    write_mcp_response({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {}
    })

def run_mcp_mode():
    """Run in MCP stdio mode"""
    
    for line in sys.stdin:
        if not line.strip():
            continue
        
        request = None
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                handle_mcp_initialize(request)
            elif method == "notifications/initialized":
                # Notification, no response needed
                pass
            elif method == "tools/list":
                handle_mcp_list_tools(request_id)
            elif method == "tools/call":
                handle_mcp_call_tool(
                    request_id,
                    params.get("name"),
                    params.get("arguments", {})
                )
            elif method == "ping":
                handle_mcp_ping(request_id)
            else:
                write_mcp_error(request_id, -32601, f"Method not found: {method}")
                
        except json.JSONDecodeError as e:
            write_mcp_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            })
        except Exception as e:
            request_id = request.get("id") if request else None
            write_mcp_error(request_id, -32603, "Internal error", str(e))

# -------------------- Command-line interface --------------------
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Diagram Server")
    parser.add_argument('--mcp', action='store_true', help='Run in MCP stdio mode')
    parser.add_argument('--http', action='store_true', help='Run in HTTP mode (default)')
    parser.add_argument('--port', type=int, default=8050, help='HTTP port (default: 8050)')
    
    args = parser.parse_args()
    
    if args.mcp:
        # Run in MCP stdio mode
        run_mcp_mode()
    else:
        # Run in HTTP mode
        import uvicorn
        print(f"Starting HTTP server on port {args.port}...")
        print("For MCP mode, use: python mcp_diagram_server.py --mcp")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
