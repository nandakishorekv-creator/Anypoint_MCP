import httpx

import os

EXCHANGE_BASE = "https://anypoint.mulesoft.com/exchange/api/v2"
CATEGORY_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/assets/{group_id}/{asset_id}/{version}/categories/{category}"
CATEGORY_GROUP_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/categories"
ASSET_CATEGORY_URL = "https://anypoint.mulesoft.com/exchange/api/v1/organizations/{org_id}/assets/{org_id}/{asset_id}/{version}/tags/categories/{category}"
ASSET_DETAILS_URL = "https://anypoint.mulesoft.com/exchange/api/v2/assets/{group_id}/{asset_id}/{version}/files"
DOWNLOAD_URL = "https://anypoint.mulesoft.com/exchange/api/{api_version}/assets/{org_id}/{asset_name}"
CREATE_APP_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/applications?apiInstanceId={api_id}"
CREATE_CONTRACT_URL = "https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/applications/{app_id}/contracts"




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
                    "displayName": category_name,
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
        """
        Add a category tag value to an asset in Anypoint Exchange.
        This allows organizing and tagging assets with custom categories.
        """
        
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

#DOWNLOAD EXTERNAL ASSET (V1 & V2 SUPPORT)
    @mcp.tool()
    async def download_exchange_asset(
        token: str,
        org_id: str,
        owner_id: str,
        asset_name: str,
        api_version: str = "v1"
    ) -> dict:
        """
        UNIVERSAL Exchange Asset Downloader (V1 & V2 smart support)

        - Downloads metadata from Exchange (v1 or v2)
        - Returns classifiers, packaging, externalLink URLs, checksums
        - Automatically detects missing fields
        - Works for ANY asset:
            ✓ RAML/OAS assets
            ✓ Fragments
            ✓ Parent POMs
            ✓ Connectors
            ✓ Maven libs
            ✓ Templates

        Parameters:
            token       : Bearer token
            org_id      : Organization ID
            owner_id    : User ID (x-owner-id)
            asset_name  : Asset to download (ex: "istika-parent-pom-new")
            api_version : "v1" or "v2"
        """

        # Build dynamic URL
        url = f"https://anypoint.mulesoft.com/exchange/api/{api_version}/assets/{org_id}/{asset_name}"

        headers = {
            "Authorization": f"Bearer {token}",
            "x-owner-id": owner_id,
            "x-organization-id": org_id,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                # In v2 assets are inside "files" → same structure
                files = data.get("files", [])

                extracted = []
                for f in files:
                    extracted.append({
                        "classifier": f.get("classifier"),
                        "packaging": f.get("packaging"),
                        "externalLink": f.get("externalLink"),
                        "md5": f.get("md5"),
                        "sha1": f.get("sha1"),
                        "downloadURL": f.get("downloadURL")
                    })

                return {
                    "status": "success",
                    "api_version": api_version,
                    "asset": asset_name,
                    "files": extracted,
                    "raw": data
                }

            except Exception as e:
                return {"status": "error", "message": str(e)}


    #Create Application
    @mcp.tool()
    async def create_application(
        token: str,
        org_id: str,
        api_instance_id: str, 
        app_name: str,
        description: str,
        url: str = "http://example.com"
        
        
    ) -> dict:
        """
        Create a Client Application in Anypoint Exchange.
        Required to obtain Client ID/Secret before requesting access.
        """
        
        url = CREATE_APP_URL.format(
            org_id=org_id, 
            api_id=api_instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {"apiInstanceId": api_instance_id}

        payload = {
            "name": app_name,
            "description": description,
            "url": url,
            "redirectUri": [], 
            "grantTypes": [],
            "apiEndpoints": False
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url, 
                    headers=headers, 
                    params=params, 
                    json=payload, 
                    timeout=40.0
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return {"status": "error", "message": str(e)}
            
            
    #CREATE API CONTRACT
    @mcp.tool()
    async def create_api_contract(
        token: str,
        org_id: str,
        app_id: str,
        api_instance_id: str,
        asset_id: str,
        group_id: str,              
        asset_version: str,
        version: str = "v1",        
        tier_id: int | None = None  
    ) -> dict:
        """
        Create API contract (Request Access) for an Application.
        """
        # URL: .../organizations/{orgId}/applications/{appId}/contracts
        url = CREATE_CONTRACT_URL.format(
            org_id=org_id,
            app_id=app_id
        )  

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "apiId": api_instance_id,
            "instanceType": "api",
            "acceptedTerms": True,
            "organizationId": org_id,
            "groupId": group_id,         # Fixed: Uses actual group_id
            "assetId": asset_id,
            "version": asset_version,
            "versionGroup": version # Fixed: Uses actual version_group
        }

        # Only add tier if the user provided it (Required for SLA-based policies)
        if tier_id is not None:
            payload["requestedTierId"] = tier_id

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=40.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                # Return valid JSON error so the Agent knows what happened
                return {"status": "error", "message": str(e)}
    