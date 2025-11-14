import httpx

ANYPOINT_TOKEN_URL = "https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token"


def register(mcp):
    @mcp.tool()
    async def get_token(client_id: str, client_secret: str) -> str:
        """Get OAuth client credentials token from Anypoint Platform."""

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

