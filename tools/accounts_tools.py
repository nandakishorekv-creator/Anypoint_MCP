import httpx

ANYPOINT_TOKEN_URL = "https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token"

# Get Token Tool
def register(mcp):
    @mcp.tool()
    async def get_token(client_id: str, client_secret: str) -> str:
        """Get User token from Client Credentials Anypoint Platform."""

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(ANYPOINT_TOKEN_URL, data=payload)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                return f"Error fetching token: {exc}"

