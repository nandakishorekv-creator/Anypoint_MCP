# Anypoint Platform MCP Server

## Overview
This MCP (Model Context Protocol) server provides automated access to MuleSoft Anypoint Platform APIs. It includes 7 tool modules with a total of **25 tools** for managing Anypoint resources.

---

## 1. LOGIN TOOLS (`login_tools.py`)
**Purpose:** Authentication and user identity management

### 1.1 `get_user_token(username: str, password: str) -> str`
- **Description:** Login to Anypoint Platform using username + password
- **Returns:** USER TOKEN and USER ID (required for Design Center operations)
- **Endpoint:** `POST https://anypoint.mulesoft.com/accounts/login`
- **Use Case:** Initial authentication to obtain bearer tokens

### 1.2 `get_user_info(token: str) -> str`
- **Description:** Fetch authenticated user's identity info from Anypoint Platform
- **Returns:** 
  - User ID
  - Username
  - Email
  - Organization memberships
  - Profile details
- **Endpoint:** `GET https://anypoint.mulesoft.com/accounts/api/me`
- **Use Case:** Retrieve profile information for currently authenticated user

---

## 2. ACCOUNTS TOOLS (`accounts_tools.py`)
**Purpose:** OAuth token management for service-to-service authentication

### 2.1 `get_token(client_id: str, client_secret: str) -> str`
- **Description:** Get OAuth client credentials token from Anypoint Platform
- **Returns:** Bearer token with access_token, expires_in, token_type
- **Endpoint:** `POST https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token`
- **Authentication Method:** Client Credentials flow
- **Use Case:** Service-to-service authentication without user login

---

## 3. EXCHANGE TOOLS (`exchange_tools.py`)
**Purpose:** Anypoint Exchange asset management and organization

### 3.1 `get_organization_assets(token: str, org_id: str) -> str`
- **Description:** List all assets in Anypoint Exchange for a given organization
- **Returns:** JSON containing all organization assets
- **Endpoint:** `GET https://anypoint.mulesoft.com/exchange/api/v2/assets`
- **Use Case:** Discover and inventory all available assets in organization

### 3.2 `get_asset_details(token: str, org_id: str, asset_id: str, version: str) -> str`
- **Description:** Get detailed information about a specific asset in Anypoint Exchange
- **Returns:** Asset metadata including description, files, versions
- **Endpoint:** `GET https://anypoint.mulesoft.com/exchange/api/v2/assets/{org_id}/{asset_id}/{version}/asset`
- **Use Case:** Retrieve comprehensive asset information before deploying

### 3.3 `create_exchange_category_group(token: str, org_id: str, category_name: str, values: list, asset_types: list = None) -> dict`
- **Description:** Create an Exchange Category Group using v2 categories API
- **Parameters:**
  - `category_name`: Display name for category group
  - `values`: List of accepted values for this category
  - `asset_types`: Restrictions (default: ["rest-api"])
- **Returns:** Category group details
- **Endpoint:** `POST https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/categories`
- **Use Case:** Establish custom categorization schema for assets

### 3.4 `add_exchange_category(token: str, org_id: str, asset_id: str, version: str, category: str, value: str) -> dict`
- **Description:** Add a category tag value to an asset in Anypoint Exchange
- **Returns:** Success status
- **Endpoint:** `PUT https://anypoint.mulesoft.com/exchange/api/v1/organizations/{org_id}/assets/{org_id}/{asset_id}/{version}/tags/categories/{category}`
- **Use Case:** Tag and organize assets with custom categories

### 3.5 `download_exchange_asset(token: str, org_id: str, owner_id: str, asset_name: str, api_version: str = "v1") -> dict`
- **Description:** Universal Exchange Asset Downloader (V1 & V2 smart support)
- **Supported Asset Types:**
  - RAML/OAS assets
  - Fragments
  - Parent POMs
  - Connectors
  - Maven libraries
  - Templates
- **Returns:** 
  - Asset metadata (classifiers, packaging, external links)
  - File checksums (md5, sha1)
  - Download URLs
- **Endpoint:** `GET https://anypoint.mulesoft.com/exchange/api/{api_version}/assets/{org_id}/{asset_name}`
- **Use Case:** Download and retrieve asset specifications for integration

### 3.6 `create_application(token: str, org_id: str, api_instance_id: str, app_name: str, description: str, url: str = "http://example.com") -> dict`
- **Description:** Create a Client Application in Anypoint Exchange
- **Returns:** Application details including client ID/secret
- **Endpoint:** `POST https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/applications?apiInstanceId={api_id}`
- **Prerequisites:** Must create before requesting API access
- **Use Case:** Generate credentials for API consumers

### 3.7 `create_api_contract(token: str, org_id: str, app_id: str, api_instance_id: str, asset_id: str, group_id: str, asset_version: str, version: str = "v1", tier_id: int | None = None) -> dict`
- **Description:** Create API contract (Request Access) for an Application
- **Parameters:**
  - `tier_id`: Required if API uses SLA tiers
  - `version`: API version (cannot assume "v1")
- **Returns:** Contract confirmation with terms
- **Endpoint:** `POST https://anypoint.mulesoft.com/exchange/api/v2/organizations/{org_id}/applications/{app_id}/contracts`
- **Use Case:** Grant API access to consumer applications

---

## 4. DESIGN CENTER TOOLS (`designcentre_tools.py`)
**Purpose:** API design, project management, and publishing

### 4.1 `create_and_lock_design_project(token: str, org_id: str, user_id: str, project_name: str, main_file: str = "api.raml") -> dict`
- **Description:** Create a Design Center project AND automatically acquire lock
- **Returns:** Project ID and project details
- **Endpoint:** 
  - CREATE: `POST https://anypoint.mulesoft.com/designcenter/api-designer/projects`
  - LOCK: `POST https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/acquireLock`
- **Flow:** Creates project → Acquires master branch lock
- **Use Case:** Initialize new API design projects with immediate edit access

### 4.2 `create_design_fragment_project(project_name: str, token: str, org_id: str, owner_id: str, description: str, subtype: str) -> dict`
- **Description:** Create a RAML Fragment Design Center project AND acquire lock automatically
- **Subtype Options:** "type", "trait", "resourceType", "library"
- **Returns:** Project ID and lock confirmation
- **Use Case:** Create reusable RAML fragments for composition
- **Special Handling:** 2-second wait for git repository initialization

### 4.3 `list_design_projects(token: str, org_id: str, user_id: str) -> str`
- **Description:** List all Design Center projects for the given organization and user
- **Returns:** JSON with all project details
- **Endpoint:** `GET https://anypoint.mulesoft.com/designcenter/api-designer/projects`
- **Note:** Requires user token (NOT client credentials token)
- **Use Case:** Inventory all projects for organization/user

### 4.4 `upload_design_files(token: str, org_id: str, user_id: str, project_id: str, folder_path: str) -> str`
- **Description:** Upload RAML files and supporting files from a folder to Design Center project
- **Behavior:**
  - Recursively walks folder structure
  - Skips `exchange_modules` directory
  - Preserves relative paths
- **Endpoint:** `POST https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/save/v2`
- **Use Case:** Bulk import RAML specifications into Design Center

### 4.5 `publish_design_project(token: str, org_id: str, user_id: str, project_id: str, main_file: str, api_version: str, version: str, asset_id: str, classifier: str = "raml") -> str`
- **Description:** Publish the Design Center project to Anypoint Exchange
- **Returns:** Publication confirmation
- **Endpoint:** `POST https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/publish/exchange`
- **Use Case:** Make API specifications available in Exchange after design

---

## 5. API MANAGER TOOLS (`api_manager_tools.py`)
**Purpose:** API instance management, policies, and SLA tier management

### 5.1 `create_api_instance_simple(token: str, org_id: str, env_id: str, group_id: str, asset_id: str, version: str, instance_label: str = None) -> dict`
- **Description:** Create API Manager Instance using stable v1 API
- **Returns:** Instance details
- **Endpoint:** `POST https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis`
- **Configuration:** 
  - Endpoint: `https://anypoint.mulesoft.com/api/v1/`
  - Proxy URI: `http://0.0.0.0:8081/`
  - Technology: `mule4`
- **Use Case:** Deploy API specifications to API Manager

### 5.2 `list_api_instances(token: str, org_id: str, env_id: str) -> dict`
- **Description:** List all API instances in an environment
- **Returns:** Complete instance inventory with assets, apis, ids
- **Endpoint:** `GET https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis`
- **Use Case:** Discover existing API deployments in environment

### 5.3 `get_api_contracts(token: str, org_id: str, env_id: str, instance_id: str) -> dict`
- **Description:** Retrieve all contracts for a given API instance
- **Returns:** 
  - Contract count
  - List of contracts with app names, tier info, status
- **Endpoint:** `GET https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/contracts`
- **Use Case:** Track consumer applications accessing specific API

### 5.4 `apply_client_id_policy(token: str, org_id: str, env_id: str, instance_id: str, client_id_header: str = "client_id", client_secret_header: str = "client_secret", apply_to_all: bool = True, methods: list | None = None, resources: list | None = None) -> dict`
- **Description:** Apply Client ID Enforcement Policy (v1.3.3) to API instance
- **Policy Behavior:**
  - If `apply_to_all = True`: Applies to all methods & resources globally
  - If `apply_to_all = False`: Applies only to specified methods/resources
- **Returns:** Policy application status
- **Endpoint:** `POST https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/policies`
- **Use Case:** Enforce client credentials for API authentication

### 5.5 `create_sla_tier(token: str, org_id: str, env_id: str, instance_id: str, name: str, description: str, api_version_id: str, limits: list, auto_approve: bool = True, status: str = "ACTIVE") -> dict`
- **Description:** Create an SLA Tier for an API Instance
- **Parameters:**
  - `api_version_id`: Usually "v1"
  - `limits`: Rate-limit rules array
  - `auto_approve`: Auto-approve tier requests
  - `status`: ACTIVE or INACTIVE
- **Example Limits:**
  ```json
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
  ```
- **Endpoint:** `POST https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/tiers`
- **Use Case:** Define tiered rate-limiting for different consumer levels

### 5.6 `list_sla_tiers(token: str, org_id: str, env_id: str, instance_id: str) -> dict`
- **Description:** List all existing SLA tiers for an API instance
- **Returns:** 
  - List of all SLA tiers configured for the API
  - Tier details including name, description, limits, status
- **Endpoint:** `GET https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/tiers`
- **Use Case:** Inventory and review all SLA tier configurations for an API instance

### 5.7 `apply_rate_limiting_sla_policy(token: str, org_id: str, env_id: str, instance_id: str) -> dict`
- **Description:** Apply SLA-Based Rate Limiting Policy using custom expressions (e.g., query params)
- **Returns:** Policy application status
- **Endpoint:** `POST https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{org_id}/environments/{env_id}/apis/{instance_id}/policies`
- **Policy Details:**
  - Asset: `rate-limiting-sla-based` v1.3.1
  - Credentials Origin: Custom Expression
  - Client ID from: `attributes.queryParams['client_id']`
  - Client Secret from: `attributes.queryParams['client_secret']`
- **Use Case:** Implement query parameter-based rate limiting

---

## 6. RAML TOOLS (`raml_tools.py`)
**Purpose:** RAML file retrieval and management

### 6.1 `get_raml_from_link(download_url: str, main_file: str) -> str`
- **Description:** Download a RAML ZIP and return the requested file
- **Returns:** RAML file contents as string
- **Process:** 
  1. Download ZIP from provided URL
  2. Extract specified main_file
  3. Return decoded content
- **Use Case:** Retrieve RAML specifications from external download links

### 6.2 `get_raml_from_migration(migration_id: str, raml_file_path: str) -> str`
- **Description:** Read RAML directly from a migration output folder
- **Path Structure:** `intelog-be/uploads/migration_output_{migration_id}/raml-specs/{raml_file_path}`
- **Returns:** RAML file contents
- **Use Case:** Access RAML files from completed migration processes

---

## 7. ACCESS MANAGEMENT TOOLS (`access_management_tools.py`)
**Purpose:** Environment and organizational structure management

### 7.1 `list_environments(token: str, org_id: str) -> dict`
- **Description:** List all environments in an Anypoint organization and return their IDs
- **Returns:** 
  - Environment IDs
  - Names
  - Types (dev/sandbox/prod)
- **Endpoint:** `GET https://anypoint.mulesoft.com/accounts/api/organizations/{org_id}/environments`
- **Use Case:** Discover available deployment environments

---

## Complete Tool Registration

All tools are automatically registered on server startup via `tools/__init__.py`:

```python
def load_tools(mcp):
    login_tools.register(mcp)
    designcentre_tools.register(mcp)
    accounts_tools.register(mcp)
    exchange_tools.register(mcp)
    raml_tools.register(mcp)
    api_manager_tools.register(mcp)
    access_management_tools.register(mcp)
```

---

## Common Authentication Flows

### User Authentication (Interactive)
```
1. get_user_token(username, password) → TOKEN
2. get_user_info(TOKEN) → User Profile
```

### Service Authentication (Automated)
```
1. get_token(client_id, client_secret) → TOKEN
2. Use TOKEN for all API operations
```

---

## Typical Workflow Examples

### Example 1: Design & Publish API
```
1. create_and_lock_design_project() → project_id
2. upload_design_files(project_id, folder_path)
3. publish_design_project(project_id, ...) → Asset in Exchange
4. get_asset_details() → Verify publication
```

### Example 2: Create API Instance & Secure
```
1. create_api_instance_simple() → instance_id
2. create_sla_tier(instance_id) → tier_id
3. apply_client_id_policy(instance_id)
4. apply_rate_limiting_sla_policy(instance_id)
```

### Example 3: Grant API Access
```
1. create_application() → app_id, client_id/secret
2. create_api_contract(app_id, api_instance_id) → contract_id
3. get_api_contracts(instance_id) → Verify access granted
```

---

## Statistics
- **Total Tools:** 25
- **Tool Modules:** 7
- **Authentication Methods:** 2 (User token, OAuth client credentials)
- **API Endpoints:** 23
- **Supported Asset Types:** 6 (RAML/OAS assets, Fragments, Parent POMs, Connectors, Maven libraries, Templates)

