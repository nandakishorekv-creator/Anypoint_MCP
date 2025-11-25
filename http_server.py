from fastapi import FastAPI
import uvicorn
from mcp.server.fastmcp import FastMCP
from tools import load_tools

app = FastAPI(title="Anypoint MCP HTTP Server")

# Create MCP instance
mcp = FastMCP("anypoint")

# Load tools into the MCP instance
load_tools(mcp)


@app.post("/mcp/tools/list")
async def list_tools():
    """
    Uses FastMCP ToolManager to list available tools.
    """
    try:
        tools = mcp._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        return {"tools": tool_names}
    except Exception as e:
        return {"error": f"Cannot list tools: {e}"}


@app.post("/mcp/tools/call")
async def call_tool(body: dict):
    """
    Uses ToolManager.call_tool() to execute a tool.
    """
    name = body.get("name")
    args = body.get("arguments", {})

    try:
        result = await mcp._tool_manager.call_tool(name, args)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
