"""
Pytest test suite for MCP Diagram Server
"""
import pytest
from fastapi.testclient import TestClient
from mcp_diagram_server import app
import base64
import json

# Create test client
client = TestClient(app)


def test_list_tools():
    """Test the /list_tools endpoint"""
    response = client.post("/list_tools")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "tools" in data
    assert len(data["tools"]) == 3
    
    # Check tool names
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "plantuml.render" in tool_names
    assert "graphviz.render" in tool_names
    assert "mermaid.render" in tool_names
    
    # Check each tool has required fields
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "arguments" in tool


def test_plantuml_render_svg():
    """Test PlantUML rendering to SVG"""
    diagram_text = "@startuml\nAlice -> Bob: Hello\n@enduml"
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {
                "text": diagram_text,
                "format": "svg"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "result" in data
    assert data["result"]["content_type"] == "image/svg+xml"
    assert "data_base64" in data["result"]
    
    # Decode and verify it's valid SVG
    svg_data = base64.b64decode(data["result"]["data_base64"])
    assert b"<?xml" in svg_data or b"<svg" in svg_data


def test_plantuml_render_png():
    """Test PlantUML rendering to PNG"""
    diagram_text = "@startuml\nAlice -> Bob: Hello\n@enduml"
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {
                "text": diagram_text,
                "format": "png"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/png"
    assert "data_base64" in data["result"]
    
    # Verify it's PNG (starts with PNG signature)
    png_data = base64.b64decode(data["result"]["data_base64"])
    assert png_data[:8] == b"\x89PNG\r\n\x1a\n"


def test_plantuml_render_default_format():
    """Test PlantUML rendering with default format (SVG)"""
    diagram_text = "@startuml\nAlice -> Bob: Hello\n@enduml"
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {
                "text": diagram_text
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/svg+xml"


def test_plantuml_missing_text():
    """Test PlantUML with missing text argument"""
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {}
        }
    )
    assert response.status_code == 400


def test_graphviz_render_svg():
    """Test Graphviz rendering to SVG"""
    dot_text = "digraph G { A -> B }"
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": dot_text,
                "format": "svg"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/svg+xml"
    assert "data_base64" in data["result"]
    
    # Decode and verify it's valid SVG
    svg_data = base64.b64decode(data["result"]["data_base64"])
    assert b"<?xml" in svg_data or b"<svg" in svg_data


def test_graphviz_render_png():
    """Test Graphviz rendering to PNG"""
    dot_text = "digraph G { A -> B }"
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": dot_text,
                "format": "png"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/png"
    assert "data_base64" in data["result"]
    
    # Verify it's PNG
    png_data = base64.b64decode(data["result"]["data_base64"])
    assert png_data[:8] == b"\x89PNG\r\n\x1a\n"


def test_graphviz_render_default_format():
    """Test Graphviz rendering with default format (PNG)"""
    dot_text = "digraph G { A -> B }"
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": dot_text
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/png"


def test_graphviz_missing_dot():
    """Test Graphviz with missing dot argument"""
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {}
        }
    )
    assert response.status_code == 400


def test_graphviz_complex_diagram():
    """Test Graphviz with a more complex diagram"""
    dot_text = """
    digraph G {
        rankdir=LR
        A[label="Start"]
        B[label="Process"]
        C[label="End"]
        A -> B -> C
    }
    """
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": dot_text,
                "format": "svg"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


@pytest.mark.skipif(
    not __import__('shutil').which('mmdc') and not __import__('shutil').which('npx'),
    reason="Mermaid CLI not available"
)
def test_mermaid_render_png():
    """Test Mermaid rendering to PNG (requires mermaid-cli)"""
    mermaid_text = "graph TD\nA --> B"
    response = client.post(
        "/call_tool",
        json={
            "name": "mermaid.render",
            "arguments": {
                "text": mermaid_text,
                "format": "png"
            }
        }
    )
    # This might fail if mmdc is not installed, which is expected
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["content_type"] == "image/png"
        assert "data_base64" in data["result"]
    else:
        # If it fails, it should be due to mmdc not found
        data = response.json()
        assert data["ok"] is False
        assert "error" in data


@pytest.mark.skipif(
    not __import__('shutil').which('mmdc') and not __import__('shutil').which('npx'),
    reason="Mermaid CLI not available"
)
def test_mermaid_render_svg():
    """Test Mermaid rendering to SVG (requires mermaid-cli)"""
    mermaid_text = "graph TD\nA --> B"
    response = client.post(
        "/call_tool",
        json={
            "name": "mermaid.render",
            "arguments": {
                "text": mermaid_text,
                "format": "svg"
            }
        }
    )
    # This might fail if mmdc is not installed
    if response.status_code == 200:
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["content_type"] == "image/svg+xml"
        assert "data_base64" in data["result"]
    else:
        data = response.json()
        assert data["ok"] is False


def test_mermaid_missing_text():
    """Test Mermaid with missing text argument"""
    response = client.post(
        "/call_tool",
        json={
            "name": "mermaid.render",
            "arguments": {}
        }
    )
    assert response.status_code == 400


def test_nonexistent_tool():
    """Test calling a non-existent tool"""
    response = client.post(
        "/call_tool",
        json={
            "name": "nonexistent.tool",
            "arguments": {}
        }
    )
    assert response.status_code == 404


def test_invalid_request_format():
    """Test with invalid request format"""
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render"
            # Missing arguments
        }
    )
    # Should return 400 for validation error
    assert response.status_code == 400


def test_plantuml_complex_diagram():
    """Test PlantUML with a more complex diagram"""
    diagram_text = """
    @startuml
    Alice -> Bob: Authentication Request
    Bob --> Alice: Authentication Response
    Alice -> Bob: Another authentication Request
    Alice <-- Bob: Another authentication Response
    @enduml
    """
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {
                "text": diagram_text.strip(),
                "format": "svg"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["result"]["content_type"] == "image/svg+xml"


def test_graphviz_invalid_syntax():
    """Test Graphviz with invalid DOT syntax"""
    invalid_dot = "digraph invalid {"
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": invalid_dot,
                "format": "svg"
            }
        }
    )
    # Should return an error
    data = response.json()
    assert data["ok"] is False
    assert "error" in data


def test_plantuml_invalid_syntax():
    """Test PlantUML with incomplete syntax"""
    invalid_text = "@startuml\nAlice -> Bob"
    response = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {
                "text": invalid_text,
                "format": "svg"
            }
        }
    )
    # PlantUML server might still try to render it
    # So we just check the response doesn't crash
    assert response.status_code in [200, 500]


def test_base64_encoding_validity():
    """Test that base64 encoded data is valid"""
    dot_text = "digraph G { A -> B }"
    response = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {
                "dot": dot_text,
                "format": "png"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    if data["ok"]:
        # Try to decode the base64
        try:
            decoded = base64.b64decode(data["result"]["data_base64"])
            assert isinstance(decoded, bytes)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Invalid base64 encoding")


@pytest.fixture
def sample_plantuml_diagram():
    """Fixture providing a simple PlantUML diagram"""
    return "@startuml\nAlice -> Bob: Test\n@enduml"


@pytest.fixture
def sample_dot_diagram():
    """Fixture providing a simple DOT diagram"""
    return "digraph G { A -> B }"


def test_render_multiple_diagrams(sample_plantuml_diagram, sample_dot_diagram):
    """Test rendering multiple different diagrams"""
    # Test PlantUML
    resp1 = client.post(
        "/call_tool",
        json={
            "name": "plantuml.render",
            "arguments": {"text": sample_plantuml_diagram, "format": "svg"}
        }
    )
    assert resp1.json()["ok"] is True
    
    # Test Graphviz
    resp2 = client.post(
        "/call_tool",
        json={
            "name": "graphviz.render",
            "arguments": {"dot": sample_dot_diagram, "format": "svg"}
        }
    )
    assert resp2.json()["ok"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
