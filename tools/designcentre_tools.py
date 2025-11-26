import httpx
import os
import asyncio
import mcp.types as types
import zipfile
import io

CREATE_PROJECT_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
LIST_PROJECTS_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects"
DESIGN_UPLOAD_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/save/v2"
IMPORT_ZIP_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/import"
LOCK_PROJECT_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/acquireLock"
EXPORT_URL = "https://anypoint.mulesoft.com/designcenter/api/designer/projects/{project_id}/branches/{branch}/archive"
PUBLISH_URL = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}/branches/master/publish/exchange"



# Create a Design Center project AND automatically acquire the lock
def register(mcp):

    @mcp.tool()
    async def create_and_lock_design_project(
        token: str,
        org_id: str,
        user_id: str,
        project_name: str,
    ) -> dict:
        """
        Create a Design Center project AND automatically acquire the lock with RETRY logic.
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
            "main": project_name + ".raml",
            "projectType": "api",
            "branchId": "master",
            "classifier": "raml"
        }

        project_id = None
        project_info = {}

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
                    return {"status": "error", "error": "Project created but ID missing."}

            except Exception as e:
                return {"status": "error", "step": "create", "error": str(e)}

            # STEP 2 — Acquire lock with RETRY LOOP
            # The master branch takes time to appear. We will try 5 times.
            lock_url = LOCK_PROJECT_URL.format(project_id=project_id)
            lock_payload = {"locked": True, "name": "locked"}
            
            max_retries = 5
            for attempt in range(1, max_retries + 1):
                print(f"Attempt {attempt}/{max_retries}: Acquiring lock for {project_id}...")
                
                try:
                    # Wait before trying (essential for the first attempt too)
                    await asyncio.sleep(3) 

                    lock_resp = await client.post(
                        lock_url,
                        headers=headers,
                        json=lock_payload,
                        timeout=30.0
                    )
                    
                    if lock_resp.status_code == 200:
                        # Double check the response implies success
                        lock_data = lock_resp.json()
                        return {
                            "status": "success",
                            "message": "Lock acquired successfully.",
                            "project_id": project_id,
                            "lock_info": lock_data,
                            "project_details": project_info
                        }
                    elif lock_resp.status_code == 403:
                        # Already locked by someone else?
                        return {
                            "status": "error",
                            "message": "Project is already locked by another user.",
                            "details": lock_resp.text
                        }
                    else:
                        print(f"Lock failed with {lock_resp.status_code}. Retrying...")

                except Exception as e:
                    print(f"Lock attempt failed: {e}")

            # If we exit the loop, we failed to lock
            return {
                "status": "partial_success",
                "message": "Project created, but failed to acquire lock after multiple retries.",
                "project_id": project_id,
                "hint": "You must manually acquire the lock in Design Center or use the retry tool."
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
    
# upload RAML files to a Design Center project
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
        
        Fixes applied:
        1. Normalizes Windows paths (backslashes) to forward slashes.
        2. Uses explicit list of tuples for multipart upload to satisfy API requirements.
        3. Better error handling and memory efficiency.
        """

        url = DESIGN_UPLOAD_URL.format(project_id=project_id)

        # Validate folder exists
        if not os.path.exists(folder_path):
            return f"Error: Folder path '{folder_path}' does not exist"
        
        if not os.path.isdir(folder_path):
            return f"Error: Path '{folder_path}' is not a directory"

        # Collect files with better error handling
        files_payload = []

        try:
            for root, dirs, files in os.walk(folder_path):
                # Skip exchange_modules
                if "exchange_modules" in root:
                    continue

                for file in files:
                    file_path = os.path.join(root, file)

                    # Get relative path and normalize
                    relative_path = os.path.relpath(file_path, folder_path)
                    normalized_path = relative_path.replace(os.sep, "/")

                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                        files_payload.append((normalized_path, (normalized_path, content)))
                    except Exception as file_error:
                        return f"Error reading file '{file_path}': {file_error}"

        except Exception as walk_error:
            return f"Error traversing directory '{folder_path}': {walk_error}"

        # Check if any files were found
        if not files_payload:
            return "Error: No files found to upload (excluding exchange_modules)"

        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files_payload,
                    timeout=60.0
                )
                response.raise_for_status()
                return f"Upload successful: {len(files_payload)} files uploaded. Response: {response.text}"
            except httpx.HTTPStatusError as e:
                return f"HTTP Error uploading files: {e.response.status_code} - {e.response.text}"
            except httpx.TimeoutException:
                return "Error: Request timeout while uploading files"
            except Exception as e:
                return f"Error uploading project files: {str(e)}"
            
# Import a Design Center Project from a local ZIP file
    @mcp.tool()
    async def import_design_project_from_zip(
        token: str,
        org_id: str,
        user_id: str,
        project_name: str,
        zip_file_path: str,
        description: str = "Imported via MCP",
        main_file: str = "api.raml",
        project_type: str = "raml",
        dependencies: str = None
    ) -> dict:
        """
        Creates a Design Center project by importing a ZIP file.
        - Automatically flattens nested folders in the ZIP.
        - Explicitly sets the Root File (main file) after import.
        """
        
        # 1. Validate Input Path
        if not os.path.exists(zip_file_path):
            return {"status": "error", "message": f"Path not found: {zip_file_path}"}
        if not os.path.isfile(zip_file_path):
            return {"status": "error", "message": f"Path is not a file: {zip_file_path}"}

        import_url = "https://anypoint.mulesoft.com/designcenter/api-designer/projects/import"

        # Base headers (Content-Type will be set automatically for multipart)
        headers = {
            "Authorization": f"Bearer {token}",
            "x-organization-id": org_id,
            "x-owner-id": user_id
        }

        # Prepare form fields for Import
        data = {
            "name": project_name,
            "description": description,
            "type": project_type,
            "mainFile": main_file
        }
        if dependencies:
            data["dependencies"] = dependencies

        async with httpx.AsyncClient() as client:
            try:
                file_content = None
                
                # 2. Analyze and Flatten ZIP if necessary
                with zipfile.ZipFile(zip_file_path, 'r') as z_in:
                    file_list = z_in.namelist()
                    
                    # Detect if all files are inside a single top-level directory
                    roots = set()
                    for name in file_list:
                        parts = name.split('/')
                        if len(parts) > 1 or name.endswith('/'):
                            roots.add(parts[0])
                        else:
                            roots.add('.')
                    
                    # If we have exactly 1 top-level folder (and it's not current dir)
                    if len(roots) == 1 and '.' not in roots:
                        root_folder = list(roots)[0] + "/"
                        print(f"Creating flattened ZIP (Removing root folder: {root_folder})...")
                        
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z_out:
                            for item in z_in.infolist():
                                if item.filename.startswith(root_folder) and item.filename != root_folder:
                                    original_content = z_in.read(item.filename)
                                    new_filename = item.filename[len(root_folder):]
                                    z_out.writestr(new_filename, original_content)
                        
                        zip_buffer.seek(0)
                        file_content = zip_buffer.read()
                    else:
                        print("ZIP structure is already flat. Uploading as-is...")
                        with open(zip_file_path, "rb") as f:
                            file_content = f.read()

                # 3. Upload (Import Project)
                files = {
                    "zipFile": (os.path.basename(zip_file_path), file_content, "application/zip")
                }

                resp = await client.post(
                    import_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=60.0
                )
                
                if resp.status_code in [200, 201]:
                    project_data = resp.json()
                    project_id = project_data.get("id")
                    
            
                    if project_id:
                        print(f"Explicitly setting root file to '{main_file}'...")
                        update_url = f"https://anypoint.mulesoft.com/designcenter/api-designer/projects/{project_id}"
                        
                        # Need explicit JSON headers for PUT
                        json_headers = headers.copy()
                        json_headers["Content-Type"] = "application/json"
                        
                        update_payload = {"main": main_file}
                        
                        update_resp = await client.put(
                            update_url,
                            headers=json_headers,
                            json=update_payload,
                            timeout=20.0
                        )
                        
                        if update_resp.status_code == 200:
                            print("Root file set successfully.")
                            project_data["main"] = main_file # Update local object
                        else:
                            print(f"Warning: Failed to set root file. API Status: {update_resp.status_code}")

                    return {
                        "status": "success", 
                        "message": "Project imported and root file set successfully.",
                        "project": project_data
                    }
                
                return {
                    "status": "error",
                    "code": resp.status_code,
                    "message": resp.text
                }

            except Exception as e:
                return {"status": "error", "message": str(e)}
    

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

