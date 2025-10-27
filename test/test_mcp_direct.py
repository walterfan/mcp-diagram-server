#!/usr/bin/env python3
"""
Test the built-in MCP mode of mcp_diagram_server.py
"""
import json
import subprocess
import sys

def test_mcp_mode():
    """Test the MCP protocol directly"""
    print("Testing MCP mode in mcp_diagram_server.py...\n")
    
    # Start the server in MCP mode
    proc = subprocess.Popen(
        ["python3", "mcp_diagram_server.py", "--mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
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
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        response = proc.stdout.readline()
        data = json.loads(response)
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2024-11-05"
        print("   ✅ Initialize passed")
        
        # Test 2: Tools list
        print("2. Testing tools/list...")
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
        assert len(data["result"]["tools"]) == 3
        print("   ✅ Tools list passed")
        
        # Test 3: Ping
        print("3. Testing ping...")
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
        print("   ✅ Ping passed")
        
        print("\n✅ All MCP tests passed!")
        return True
        
    finally:
        proc.terminate()

if __name__ == "__main__":
    test_mcp_mode()
