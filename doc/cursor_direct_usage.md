# Using MCP Diagram Server Directly in Cursor

## ✅ Answer: YES, No Python Script Needed!

Cursor can **directly call** the MCP diagram server without you needing to write any Python scripts!

## How It Works

Once configured, the MCP server exposes tools to Cursor's AI, and you can simply ask:

```
"Generate a PlantUML sequence diagram showing user login flow"
"Create a Graphviz architecture diagram for a microservices system"
"Draw a Mermaid flowchart for the checkout process"
```

**Cursor will automatically:**
1. Call the MCP server
2. Execute the diagram rendering
3. Return the image to you
4. Display it inline in the conversation

**No intermediate Python scripts needed!**

## Configuration

Your `~/.cursor/mcp.json` should have:

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

## Using Poetry (Recommended)

If you're using Poetry for dependency management:

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
      "env": {
        "PATH": "/path/to/poetry/env/bin:${PATH}"
      }
    }
  }
}
```

## Example Conversations

### Example 1: PlantUML Sequence Diagram
**You:** "Create a PlantUML sequence diagram showing a user logging into a system"

**Cursor:** *Automatically calls `plantuml.render` tool and displays the diagram*

### Example 2: Graphviz Architecture
**You:** "Generate a Graphviz diagram for a microservices architecture with Load Balancer, API Gateway, and three microservices"

**Cursor:** *Calls `graphviz.render` tool and shows the diagram*

### Example 3: Mermaid Flowchart
**You:** "Draw a Mermaid flowchart for order processing workflow"

**Cursor:** *Uses `mermaid.render` tool to generate the flowchart*

## What You DON'T Need to Do

❌ Don't write a Python script  
❌ Don't call the HTTP API manually  
❌ Don't import requests and make HTTP calls  
❌ Don't save intermediate code  

## What You DO Need to Do

✅ Configure the MCP server in Cursor settings  
✅ Ask Cursor to generate diagrams  
✅ Cursor handles everything automatically  

## Behind the Scenes

When you ask Cursor to generate a diagram:

```
You → Cursor AI → MCP Server → Renderer → Image → Cursor → You
```

1. You ask: "Create a PlantUML diagram..."
2. Cursor AI: Recognizes it needs a diagram
3. Cursor AI: Calls MCP server's `plantuml.render` tool
4. MCP Server: Renders the diagram
5. MCP Server: Returns the SVG/PNG
6. Cursor AI: Displays it to you

**All automated!** 🎉

## Available Tools

The MCP server exposes these tools automatically:

1. **`plantuml.render`**
   - Arguments: `text` (PlantUML code), `format` (svg/png)
   
2. **`graphviz.render`**
   - Arguments: `dot` (DOT code), `format` (svg/png)
   
3. **`mermaid.render`**
   - Arguments: `text` (Mermaid code), `format` (svg/png)

## Restart Cursor

After updating the configuration, restart Cursor to load the new MCP server.

## Verification

To check if the server is loaded:

1. Open Cursor
2. Start a conversation
3. Ask: "What MCP tools are available?"
4. Cursor should list the three render tools

## Summary

**Before:** Had to write Python scripts, call APIs, handle responses  
**After:** Just ask Cursor to generate diagrams - it handles everything!

This is the power of MCP - it provides a standardized interface so AI assistants can directly use tools without custom integration code.

