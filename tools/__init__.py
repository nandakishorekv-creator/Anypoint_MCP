from . import accounts_tools, exchange_tools, login_tools, raml_tools, designcentre_tools


def load_tools(mcp):
    """
    Register all FastMCP tools with the shared MCP instance.
    """
    login_tools.register(mcp)
    designcentre_tools.register(mcp)
    accounts_tools.register(mcp)
    exchange_tools.register(mcp)
    raml_tools.register(mcp)

    
    
