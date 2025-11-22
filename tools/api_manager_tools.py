import httpx


API_INSTANCE_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis"
LIST_APIS_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis"
API_CONTRACTS_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/contracts"
API_CONTRACT_DETAIL_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/contracts/{contract_id}"
POLICY_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/policies"
SLA_TIER_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/tiers"
LIST_SLA_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/tiers"
CREATE_SLA_TIER_URL = "https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/tiers"

#Create API INSTANCE
def register(mcp):
    @mcp.tool()
    async def create_api_instance(
        token: str,
        org_id: str,
        env_id: str,
        group_id: str,
        asset_id: str,
        version: str,
        instance_label: str = None
    ) -> dict:
        """
        Create API Manager Instance using the proven stable v1 API.
        This is the same structure used in your Node.js automation.
        """

        if instance_label is None:
            instance_label = f"{asset_id}_instance"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "instanceLabel": instance_label,

            "spec": {
                "groupId": group_id,
                "assetId": asset_id,
                "version": version
            },

            "endpoint": {
                "uri": "https://anypoint.mulesoft.com/api/v1/",
                "proxyUri": "http://0.0.0.0:8081/",
                "isCloudHub": True
            },

            "technology": "mule4"
        }

        url = API_INSTANCE_URL.format(org_id=org_id, env_id=env_id)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
                resp.raise_for_status()
                return {
                    "status": "success",
                    "instance": resp.json()
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}


    #LIST API INTSANCES
    @mcp.tool()
    async def list_api_instances(
        token: str,
        org_id: str,
        env_id: str
    ) -> dict:
        """
        List all API instances in an environment.
        Equivalent to instanceList in the Node.js automation.
        """

        url = LIST_APIS_URL.format(org_id=org_id, env_id=env_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=40.0)
                resp.raise_for_status()
                return resp.json()   # contains assets[], apis[], ids, etc.
            except Exception as e:
                return {"error": str(e)}


# List API contract and get Contract Details
    @mcp.tool()
    async def list_api_contracts(
        token: str,
        org_id: str,
        env_id: str,
        instance_id: str
    ) -> dict:
        """
        Retrieve all contracts for a given API instance.
        """
        url = API_CONTRACTS_URL.format(
            org_id=org_id,
            env_id=env_id,
            instance_id=instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                # The list endpoint usually contains all necessary details (App name, Tier, Status)
                resp = await client.get(url, headers=headers, timeout=30.0)
                resp.raise_for_status()
                
                data = resp.json()
                
                # Helper to standardize output if 'contracts' key is missing or nested
                contracts = data.get("contracts", data) if isinstance(data, dict) else data

                return {
                    "status": "success",
                    "count": len(contracts),
                    "contracts": contracts
                }

            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        
#CLIENT ID ENFORCMENT
    @mcp.tool()
    async def apply_client_id_policy(
        token: str,
        org_id: str,
        env_id: str,
        instance_id: str,
        client_id_header: str = "client_id",
        client_secret_header: str = "client_secret",
        apply_to_all: bool = True,
        methods: list | None = None,
        resources: list | None = None
    ) -> dict:
        """
        Apply Client ID Enforcement Policy (1.3.3) to an API instance.

        If apply_to_all = True:
            Policy applies to all methods & all resources automatically.

        If apply_to_all = False:
            You must pass:
                - methods: ["GET", "POST"]
                - resources: ["/users", "/orders/{id}"]
        """

        url = POLICY_URL.format(
            org_id=org_id,
            env_id=env_id,
            instance_id=instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # --- Build pointcutData ---
        if apply_to_all:
            pointcut = [
                {
                    "apiVersionId": instance_id,
                    "methodRegex": ".*",
                    "resourceRegex": ".*",
                    "uriTemplateRegex": ".*"
                }
            ]
        else:
            # Build specific method/resource patterns
            method_regex = "|".join(methods) if methods else ".*"
            resource_regex = "|".join(resources) if resources else ".*"

            pointcut = [
                {
                    "apiVersionId": instance_id,
                    "methodRegex": method_regex,
                    "resourceRegex": resource_regex,
                    "uriTemplateRegex": resource_regex
                }
            ]

        # --- Build payload ---
        payload = {
            "groupId": "68ef9520-24e9-4cf2-b2f5-620025690913",  # Static MuleSoft group for all policies
            "assetId": "client-id-enforcement",
            "assetVersion": "1.3.3",

            "configurationData": {
                "credentialsOrigin": "customExpression",
                "credentialsOriginHasHttpBasicAuthenticationHeader": "customExpression",

                "clientIdExpression": f"#[attributes.headers['{client_id_header}']]",
                "clientSecretExpression": f"#[attributes.headers['{client_secret_header}']]",

                "delayAttempts": 1,
                "queuingLimit": 5,
                "exposeHeaders": False
            },

            "pointcutData": pointcut
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return {"status": "success", "response": resp.json()}
            except Exception as e:
                return {"status": "error", "message": str(e)}
            

#Create SLA TIER
    @mcp.tool()
    async def create_sla_tier(
        token: str,
        org_id: str,
        env_id: str,
        instance_id: str,
        name: str,
        description: str,
        api_version_id: str,
        limits: list,
        auto_approve: bool = False,
        status: str = "ACTIVE"
    ) -> dict:
        """
        Create an SLA Tier for an API Instance.

        Required parameters:
        - token: OAuth bearer token
        - org_id: Anypoint Organization ID
        - env_id: Environment ID
        - instance_id: API Manager instance ID
        - name: SLA tier name
        - description: Tier description
        - api_version_id: Usually "v1"
        - limits: List of rate-limits (each has visible, maximumRequests, timePeriodInMilliseconds)
        - auto_approve: Boolean (default True)
        - status: ACTIVE or INACTIVE

        Example limits:
        [
            {
                "visible": true,
                "timePeriodInMilliseconds": 36000000,
                "maximumRequests": 10
            },
            {
                "visible": true,
                "maximumRequests": 20,
                "timePeriodInMilliseconds": 1800000
            }
        ]
        """

        url = CREATE_SLA_TIER_URL.format(
            org_id=org_id,
            env_id=env_id,
            instance_id=instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "apiVersionId": api_version_id,
            "status": status,
            "autoApprove": auto_approve,
            "limits": limits,
            "name": name,
            "description": description
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=40)
                resp.raise_for_status()
                return {"status": "success", "response": resp.json()}
            except Exception as e:
                return {"status": "error", "message": str(e)}


#LIST SLA TIER
    @mcp.tool()
    async def list_sla_tiers(
        token: str,
        org_id: str,
        env_id: str,
        instance_id: str
    ) -> dict:
        """
        List all existing SLA tiers for an API instance.
        """

        url = LIST_SLA_URL.format(
            org_id=org_id,
            env_id=env_id,
            instance_id=instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                return {"status": "success", "tiers": resp.json()}
            except Exception as e:
                return {"status": "error", "message": str(e)}
            
#APPLY SLA BASED POLICY
    @mcp.tool()
    async def apply_sla_rate_limiting_(
        token: str,
        org_id: str,
        env_id: str,
        instance_id: str,

    ) -> dict:
        """
        Apply SLA-Based Rate Limiting Policy using Custom Expressions (e.g., Query Params).
        
        Args:
            token: Anypoint Bearer Token
            org_id: Organization ID
            env_id: Environment ID
            instance_id: API Instance ID
        """

        url = POLICY_URL.format(
            org_id=org_id,
            env_id=env_id,
            instance_id=instance_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "groupId": "68ef9520-24e9-4cf2-b2f5-620025690913",
            "assetId": "rate-limiting-sla-based",
            "assetVersion": "1.3.1",
            "configurationData": {
                "credentialsOrigin": "customExpression",
                "clientIdExpression": "#[attributes.queryParams['client_id']]",
                "clientSecretExpression": "#[attributes.queryParams['client_secret']]"
            },
            "pointcutData": None, 
            "order": 1
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=40)
                resp.raise_for_status()
                return {"status": "success", "response": resp.json()}

            except Exception as e:
                return {"status": "error", "message": str(e)}
