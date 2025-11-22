import httpx

LOGIN_URL = "https://anypoint.mulesoft.com/accounts/login"

# User Login Tool
def register(mcp):
    @mcp.tool()
    async def get_user_token(username: str, password: str) -> str:
        """
        Login to Anypoint Platform using username + password.
        Returns a USER TOKEN and USER ID required for Design Center operations.
        """

        payload = {
            "username": username,
            "password": password
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    LOGIN_URL,
                    json=payload,
                    headers=headers,
                    timeout=20.0
                )
                resp.raise_for_status()

                return resp.text  # Contains user.id and token
            except Exception as e:
                return f"Error during user login: {e}"



# Get User Info Tool
    USER_URL = "https://anypoint.mulesoft.com/accounts/api/me"

    @mcp.tool()
    async def get_user_info(token: str) -> str:
        """
        Fetch authenticated user's identity info from Anypoint Platform.
        Returns:
            - userId
            - username
            - email
            - organization memberships
            - other profile details
        """

        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    USER_URL,
                    headers=headers,
                    timeout=20.0
                )
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error fetching user info: {e}"
