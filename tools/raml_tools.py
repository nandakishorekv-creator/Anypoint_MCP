import io
import os
import zipfile
from pathlib import Path

import httpx


def register(mcp):
    @mcp.tool()
    async def get_raml_from_link(download_url: str, main_file: str) -> str:
        """
        Download a RAML ZIP and return the requested file.
        """

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(download_url, timeout=40.0)
                resp.raise_for_status()

                zip_bytes = io.BytesIO(resp.content)
                with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
                    if main_file in zip_ref.namelist():
                        return zip_ref.read(main_file).decode("utf-8")
                    return f"Main RAML file '{main_file}' not found inside the ZIP."
            except Exception as exc:
                return f"Error downloading or extracting RAML: {exc}"

    @mcp.tool()
    async def get_raml_from_migration(migration_id: str, raml_file_path: str) -> str:
        """
        Read RAML directly from a migration output folder.
        """

        project_root = Path(__file__).resolve().parent.parent
        full_path = project_root / "intelog-be" / "uploads" / f"migration_output_{migration_id}" / "raml-specs" / raml_file_path

        if not full_path.exists():
            return f"RAML file not found at: {full_path}"

        try:
            with full_path.open("r", encoding="utf-8") as handle:
                return handle.read()
        except Exception as exc:
            return f"Error reading RAML file: {exc}"

