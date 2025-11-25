from mcp.server.fastmcp import FastMCP
import uvicorn
from tools import load_tools

mcp = FastMCP("anypoint")


def main():
    load_tools(mcp)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
    