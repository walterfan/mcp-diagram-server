"""
Test package for MCP Diagram Server
"""

import sys
from pathlib import Path

# Add parent directory to path so tests can import mcp_diagram_server
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

