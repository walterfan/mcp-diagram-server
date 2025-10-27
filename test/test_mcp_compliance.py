#!/usr/bin/env python3
"""
Test script to verify MCP protocol compliance
"""
import json
import subprocess
import sys
import time

def test_initialize():
    """Test MCP initialize handshake"""
    print("Testing initialize...")
    request = {
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
    
    proc = subprocess.Popen(
        ["python3", "mcp_stdio_wrapper.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    data = json.loads(response)
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert "capabilities" in data["result"]
    print("✅ Initialize test passed")
    
    proc.terminate()

def test_tools_list():
    """Test tools/list method"""
    print("Testing tools/list...")
    
    proc = subprocess.Popen(
        ["python3", "mcp_stdio_wrapper.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()  # Consume init response
    
    # Send initialed notification
    init_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    proc.stdin.write(json.dumps(init_notif) + "\n")
    proc.stdin.flush()
    
    # Now request tools
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    proc.stdin.write(json.dumps(tools_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    data = json.loads(response)
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "tools" in data["result"]
    print("✅ Tools/list test passed")
    
    proc.terminate()

def test_ping():
    """Test ping/pong"""
    print("Testing ping...")
    
    proc = subprocess.Popen(
        ["python3", "mcp_stdio_wrapper.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    ping_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "ping"
    }
    proc.stdin.write(json.dumps(ping_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    data = json.loads(response)
    
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data
    print("✅ Ping test passed")
    
    proc.terminate()

def test_invalid_method():
    """Test error handling for invalid method"""
    print("Testing invalid method...")
    
    proc = subprocess.Popen(
        ["python3", "mcp_stdio_wrapper.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "nonexistent/method"
    }
    proc.stdin.write(json.dumps(invalid_request) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    data = json.loads(response)
    
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32601
    print("✅ Invalid method test passed")
    
    proc.terminate()

if __name__ == "__main__":
    print("Testing MCP Protocol Compliance\n")
    
    try:
        test_initialize()
        test_tools_list()
        test_ping()
        test_invalid_method()
        
        print("\n✅ All MCP compliance tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
