import asyncio

from supabase import AsyncClient
from supabase_auth.errors import AuthApiError
from dotenv import load_dotenv
from postgrest.exceptions import APIError
import friends

load_dotenv()

async_client : AsyncClient

async def login_user(email: str, password: str):
    """
    Logs the user in by checking email and password against email and hashed password.
    """
    global async_client

    try:
        response = await async_client.auth.sign_in_with_password({"email": email, "password": password})

        if friends.client and response.session:
            friends.client.auth.set_session(
                response.session.access_token,
                response.session.refresh_token,
            )

        return response
    
    except AuthApiError:
        raise RuntimeError("Login failed: Invalid email or password.")
    
async def register_user(email: str, password: str, username: str, phone_number: str = ""):
    """
    Registers the user by creating a new user in the Supabase authentication system and inserting
    the user's information into the "user_information" table in the "public" schema.
    """
    global async_client

    try:

        if phone_number:
            response = await async_client.auth.sign_up({"email": email, "password": password, "phone": phone_number, 'options': {"data": {"username": username}}})
            await async_client.auth.sign_out()
            await async_client.from_("user_information").insert({"user_id": response.user.id, "email": email, "username": username, "phone_number": phone_number}, returning="minimal").execute()

        else:
            response = await async_client.auth.sign_up({"email": email, "password": password, 'options': {"data": {"username": username}}})
            await async_client.auth.sign_out()
            await async_client.from_("user_information").insert({"user_id": response.user.id, "email": email, "username": username}, returning="minimal").execute()

        return True

    except APIError as e:
        raise RuntimeError(e.message) from e
    
    except RuntimeError as e:
        raise RuntimeError("Registration failed: invalid username or password.") from e
