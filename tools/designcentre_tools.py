import httpx
import os


DESIGN_BASE = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
LIST_PROJECTS_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
DESIGN_UPLOAD_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/save/v2"
LOCK_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/acquireLock"
EXPORT_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/master/export"




# Create a new Design Center project
def register(mcp):
    @mcp.tool()
    async def create_design_project(
        token: str,
        org_id: str,
        user_id: str,
        project_name: str,
        main_file: str = "api.raml"
    ) -> str:
        """
        Create a new Design Center API project.
        """

        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id,
            "Content-Type": "application/json"
        }

        payload = {
            "name": project_name,
            "main": main_file,
            "projectType": "api",
            "branchId": "master",
            "classifier": "raml"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    DESIGN_BASE,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error creating Design Center project: {e}"

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
    
    #Acquire Design Lock
    @mcp.tool()
    async def acquire_design_lock(
        token: str,
        org_id: str,
        user_id: str,
        project_id: str
    ) -> str:
        """
        Acquire design center project lock before uploading files.
        """

        url = LOCK_URL.format(project_id=project_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id,
            "Content-Type": "application/json"
        }

        payload = {
            "locked": True,
            "name": "locked"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=20.0
                )
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error acquiring lock: {e}"

    
    #Download Design Center Project as ZIP
    @mcp.tool()
    async def download_design_project(
        token: str,
        org_id: str,
        user_id: str,
        project_id: str,
    ) -> bytes:
        """
        Download the entire Design Center project as a ZIP file (binary).
        Returns ZIP bytes which Claude can save to disk.
        """

        url = EXPORT_URL.format(project_id=project_id)

        headers = {
            "Authorization": f"Bearer {token}",
            "x-owner-id": user_id,
            "x-organization-id": org_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, timeout=40.0)
                resp.raise_for_status()
                return resp.content    # ZIP bytes
            except Exception as e:
                return f"Error downloading project: {e}"
