#!/usr/bin/env python3
"""
Test the SSE mode of mcp_diagram_server.py
"""
import requests
import json

SERVER = "http://localhost:8050"

def test_sse_mode():
    """Test MCP SSE endpoint"""
    print("Testing MCP SSE mode...\n")
    
    endpoint = f"{SERVER}/sse"
    
    # Test 1: Initialize
    print("1. Testing initialize...")
    init_request = {
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
    }
    
    response = requests.post(endpoint, json=init_request)
    data = response.json()
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert data["result"]["protocolVersion"] == "2024-11-05"
    print("   ✅ Initialize passed")
    
    # Test 2: List tools
    print("2. Testing tools/list...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    response = requests.post(endpoint, json=tools_request)
    data = response.json()
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "tools" in data["result"]
    assert len(data["result"]["tools"]) == 3
    print("   ✅ Tools list passed")
    print(f"   Found {len(data['result']['tools'])} tools:")
    for tool in data["result"]["tools"]:
        print(f"      - {tool['name']}")
    
    # Test 3: Ping
    print("3. Testing ping...")
    ping_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "ping"
    }
    
    response = requests.post(endpoint, json=ping_request)
    data = response.json()
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data
    print("   ✅ Ping passed")
    
    # Test 4: Call a tool (PlantUML)
    print("4. Testing tools/call (plantuml.render)...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "plantuml.render",
            "arguments": {
                "text": "@startuml\nAlice -> Bob\n@enduml",
                "format": "svg"
            }
        }
    }
    response = requests.post(endpoint, json=call_request)
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 4
    assert "result" in data
    assert "content" in data["result"]
    assert len(data["result"]["content"]) >= 1
    print("   ✅ Tool call passed")
    print(f"   Content type: {data['result']['content'][1]['mimeType']}")

    # Test 5: Call a tool (Graphviz)
    print("5. Testing tools/call (graphviz.render)...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "graphviz.render",
            "arguments": {
                "dot": "digraph G { A -> B; }",
                "format": "png"
            }
        }
    }
    response = requests.post(endpoint, json=call_request)
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 5
    assert "result" in data
    assert "content" in data["result"]
    assert len(data["result"]["content"]) >= 1
    print("   ✅ Tool call passed")
    print(f"   Content type: {data['result']['content'][1]['mimeType']}")

    # Test 6: Call a tool (Mermaid)
    print("6. Testing tools/call (mermaid.render)...")
    call_request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "mermaid.render",
            "arguments": {
                "text": "graph TD; A-->B; B-->C;",
                "format": "png"
            }
        }
    }

    response = requests.post(endpoint, json=call_request)
    data = response.json()
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 6
    assert "result" in data
    assert "content" in data["result"]
    assert len(data["result"]["content"]) >= 1
    print("   ✅ Tool call passed")
    print(f"   Content type: {data['result']['content'][1]['mimeType']}")
    
    print("\n✅ All SSE tests passed!")
    return True

if __name__ == "__main__":
    import sys
    
    print("Note: Make sure the server is running:")
    print("  uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050\n")
    
    try:
        test_sse_mode()
        sys.exit(0)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print("Please start the server with:")
        print("  uvicorn mcp_diagram_server:app --host 0.0.0.0 --port 8050")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

