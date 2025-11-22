import httpx

ENV_URL = "https://anypoint.mulesoft.com/accounts/api/organizations/{org_id}/environments"

# List Environments Tool

def register(mcp):
    @mcp.tool()
    async def list_environments(token: str, org_id: str) -> dict:
        """
        List all environments in an Anypoint organization and return their IDs.
        """

        url = ENV_URL.format(org_id=org_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=40.0)
                resp.raise_for_status()
                return resp.json()   # contains id, name, type (dev/sandbox/prod)
            except Exception as e:
                return {"error": str(e)}
