from . import accounts_tools, exchange_tools, raml_tools


def load_tools(mcp):
    """
    Register all FastMCP tools with the shared MCP instance.
    """

    accounts_tools.register(mcp)
    exchange_tools.register(mcp)
    raml_tools.register(mcp)
