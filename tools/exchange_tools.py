import httpx

EXCHANGE_BASE = "https://anypoint.mulesoft.com/exchange/api/v2"


# Register Exchange-related tools

def register(mcp):

#List all assets in an organization

    @mcp.tool()
    async def get_organization_assets(token: str, org_id: str) -> str:
        """
        List all assets in Anypoint Exchange for a given organization.
        """

        url = f"{EXCHANGE_BASE}/assets"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"organizationId": org_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=headers, params=params, timeout=30.0
                )
                response.raise_for_status()
                return response.text
            except Exception as exc:
                return f"Error fetching assets: {exc}"

#Get detailed information about a specific asset

    @mcp.tool()
    async def get_asset_details(token: str, org_id: str, asset_id: str, version: str) -> str:
        """
        Get detailed information about a specific asset in Anypoint Exchange.
        """

        url = f"{EXCHANGE_BASE}/assets/{org_id}/{asset_id}/{version}/asset"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                return response.text
            except Exception as exc:
                return f"Error fetching asset details: {exc}"

#Get list of files associated with an asset

    @mcp.tool()
    async def get_asset_files(token: str, org_id: str, asset_id: str, version: str) -> str:
        """
        Get list of files associated with an asset in Anypoint Exchange.
        """

        url = f"{EXCHANGE_BASE}/assets/{org_id}/{asset_id}/{version}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=30.0)
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                return f"Error fetching asset files: {exc}"

