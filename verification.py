from supabase import create_async_client
from supabase_auth.errors import AuthApiError
from dotenv import load_dotenv
import os
from PyQt5.QtCore import pyqtSignal, QObject
import friends

load_dotenv()


async def login_user(email: str, password: str):
    """
    Logs the user in by checking email and password against email and hashed password.
    """

    try:
        client = await create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        response = await client.auth.sign_in_with_password({"email": email, "password": password})

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

    try:
        client = await create_async_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        if phone_number:
            response = await client.auth.sign_up({"email": email, "password": password, "phone": phone_number, 'options': {"data": {"username": username}}})
        else:
            response = await client.auth.sign_up({"email": email, "password": password, 'options': {"data": {"username": username}}})

        return response
    
    except:
        raise RuntimeError("Registration failed: Invalid email, password, or phone number.")


