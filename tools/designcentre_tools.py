import httpx
import os
import asyncio
import mcp.types as types

CREATE_PROJECT_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
LIST_PROJECTS_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
DESIGN_UPLOAD_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/save/v2"
LOCK_PROJECT_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/acquireLock"
EXPORT_URL = "https://anypoint.mulesoft.com/designcenter/api/designer/projects/{project_id}/branches/{branch}/archive"
PUBLISH_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/publish/exchange"



# Create a new Design Center project
def register(mcp):
    @mcp.tool()
    async def create_and_lock_design_project(
        token: str,
        org_id: str,
        user_id: str,
        project_name: str,
        main_file: str = "api.raml"
    ) -> dict:
        """
        Create a Design Center project AND automatically acquire the lock.
        This merges:
        - create_design_project
        - acquire_design_lock
        """

        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id,
            "Content-Type": "application/json"
        }

        # STEP 1 — Create project
        payload = {
            "name": project_name,
            "main": main_file,
            "projectType": "api",
            "branchId": "master",
            "classifier": "raml"
        }

        async with httpx.AsyncClient() as client:
            try:
                create_resp = await client.post(
                    CREATE_PROJECT_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                create_resp.raise_for_status()

                project_info = create_resp.json()
                project_id = project_info.get("id")

                if not project_id:
                    return {
                        "status": "error",
                        "error": "Project created but no project_id returned."
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "step": "create",
                    "error": str(e)
                }

            # STEP 2 — Acquire lock
            lock_url = LOCK_PROJECT_URL.format(project_id=project_id)

            lock_payload = {
                "locked": True,
                "name": "locked"
            }

            try:
                lock_resp = await client.post(
                    lock_url,
                    headers=headers,
                    json=lock_payload,
                    timeout=30.0
                )
                lock_resp.raise_for_status()

                return {
                    "status": "success",
                    "message": "Design project created and locked successfully.",
                    "project_id": project_id,
                    "project_details": project_info
                }

            except Exception as e:
                return {
                    "status": "partial_success",
                    "project_id": project_id,
                    "error": f"Project created but lock failed: {str(e)}"
                }

#CREATE FRAGMENT PROJECT
    @mcp.tool()
    async def create_design_fragment_project(
        project_name: str,
        token: str,
        org_id: str,
        owner_id: str,
        description: str,
        subtype: str
    ) -> dict:
        """
        Create a RAML Fragment Design Center project AND acquire lock automatically.
        subtype options: "type", "trait", "resourceType", "library"
        """
        
        # Ensure no trailing slash to avoid URL errors
        base_url = CREATE_PROJECT_URL.rstrip("/") 

        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": owner_id,
            "Content-Type": "application/json"
        }

        # STEP 1: Create the fragment project
        payload = {
            "name": project_name,
            "description": description,
            "classifier": "raml-fragment",
            "type": "raml-fragment",
            "subType": subtype
        }

        async with httpx.AsyncClient() as client:
            try:
                # 1. Create Project
                print(f"Creating project '{project_name}'...")
                resp = await client.post(base_url, headers=headers, json=payload, timeout=30)
                resp.raise_for_status()

                project = resp.json()
                project_id = project.get("id")

                if not project_id:
                    return {"status": "error", "message": "Project created but ID missing", "raw": project}

                # --- CRITICAL FIX: WAIT FOR GIT REPO INITIALIZATION ---
                # The master branch takes a moment to appear after project creation.
                print("Waiting for repository initialization...")
                await asyncio.sleep(2) 
                # ------------------------------------------------------

                # 2. Acquire Master Branch Lock
                # Note: Endpoint is usually .../projects/{id}/branches/master/acquireLock
                lock_url = f"{base_url}/{project_id}/branches/master/acquireLock"
                
                # Some versions of DC require 'force=true' or specific body. 
                # This empty/minimal payload usually works.
                lock_payload = {
                    "locked": True, 
                    "name": "locked" 
                }

                print(f"Acquiring lock on {project_id}...")
                lock_resp = await client.post(lock_url, headers=headers, json=lock_payload, timeout=30)
                
                # Custom Error Handling to see the REAL error
                if lock_resp.status_code != 200:
                    return {
                        "status": "partial_success",
                        "message": f"Project created, but Lock failed: {lock_resp.status_code}",
                        "projectId": project_id,
                        "lock_error_details": lock_resp.text # This tells you WHY (e.g. 'Branch not found')
                    }

                return {
                    "status": "success",
                    "projectId": project_id,
                    "lock": lock_resp.json(),
                    "raw": project
                }

            except httpx.HTTPStatusError as e:
                return {
                    "status": "error", 
                    "message": f"HTTP Error: {e.response.status_code}", 
                    "details": e.response.text
                }
            except Exception as e:
                return {"status": "error", "message": str(e)}


# List all Design Center projects for an organization and user
    @mcp.tool()
    async def list_design_projects(token: str, org_id: str, user_id: str) -> str:
        """
        List all Design Center projects for the given organization and user.

        Args:
            token: User token (NOT client credentials token)
            org_id: Organization ID
            user_id: User ID (x-owner-id)

        Returns:
            JSON text containing all project details
        """

        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    LIST_PROJECTS_URL,
                    headers=headers,
                    timeout=20.0
                )
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error listing Design Center projects: {e}"
    
    #upload RAML files to a Design Center project
    @mcp.tool()
    async def upload_design_files(
        token: str,
        org_id: str,
        user_id: str,
        project_id: str,
        folder_path: str
    ) -> str:
        """
        Upload RAML files and supporting files from a folder to a Design Center project.

        Args:
            token: User token
            org_id: Organization ID
            user_id: Owner/User ID
            project_id: ID of the design center project
            folder_path: Local folder path containing RAML project files
        """

        url = DESIGN_UPLOAD_URL.format(project_id=project_id)

        # Collect form-data files
        form_data = {}

        for root, dirs, files in os.walk(folder_path):
            # Skip exchange_modules
            if "exchange_modules" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)

                relative_path = os.path.relpath(file_path, folder_path)

                with open(file_path, "rb") as f:
                    form_data[relative_path] = f.read()

        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id,
        }

        multipart = {
            name: (name, content) for name, content in form_data.items()
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    files=multipart,
                    timeout=60.0
                )
                response.raise_for_status()
                return "Upload successful: " + response.text
            except Exception as e:
                return f"Error uploading project files: {e}"
    
    

    #Publish Design Center Project to Anypoint Exchange
    @mcp.tool()
    async def publish_design_project(
        token: str,
        org_id: str,
        user_id: str,
        project_id: str,
        main_file: str,
        api_version: str,
        version: str,
        asset_id: str,
        classifier: str = "raml"
    ) -> str:
        """
        Publish the uploaded Design Center project to Anypoint Exchange.
        """

        url = PUBLISH_URL.format(project_id=project_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "x-owner-id": user_id,
            "x-organization-id": org_id,
            "Content-Type": "application/json"
        }

        payload = {
            "main": main_file,
            "apiVersion": api_version,
            "version": version,
            "assetId": asset_id,
            "classifier": classifier
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=payload, timeout=40.0)
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error publishing design project: {e}"

