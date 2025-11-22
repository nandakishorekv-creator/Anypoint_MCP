import httpx

EXCHANGE_BASE = "https://anypoint.mulesoft.com/exchange/api/v2"
CATEGORY_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/assets/{group_id}/{asset_id}/{version}/categories/{category}"
CATEGORY_GROUP_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/categories"
ASSET_CATEGORY_URL = "https://anypoint.mulesoft.com/exchange/api/v1/organizations/{org_id}/assets/{org_id}/{asset_id}/{version}/tags/categories/{category}"

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
    async def create_exchange_category_group(
                token: str,
                org_id: str,
                category_name: str,
                values: list,
                asset_types: list = None
            ) -> dict:
                """
                Create an Exchange Category Group using the v2 categories API.
                """

                if asset_types is None:
                    asset_types = ["rest-api"]

                url = CATEGORY_GROUP_URL.format(org_id=org_id)

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "display_name": category_name,
                    "acceptedValues": values,
                    "assetTypeRestrictions": asset_types
                }

                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.post(url, headers=headers, json=payload, timeout=40.0)
                        resp.raise_for_status()
                        return resp.json()
                    except Exception as e:
                        return {"error": str(e)}    

#Add asset to exchange category
    @mcp.tool()
    async def add_exchange_category(
        token: str,
        org_id: str,
        asset_id: str,
        version: str,
        category: str,
        value: str
    ) -> dict:
        
        url = ASSET_CATEGORY_URL.format(
            org_id=org_id,
            asset_id=asset_id,
            version=version,
            category=category
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "tagValue": [value]
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.put(url, headers=headers, json=payload, timeout=40.0)
                resp.raise_for_status()
                return {"status": "Category added successfully"}
            except Exception as e:
                return {"error": str(e)}

