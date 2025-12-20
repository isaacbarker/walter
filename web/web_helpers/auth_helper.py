import os
from dotenv import load_dotenv, find_dotenv

# Checks the client is properly authenticated with the correct token

# Environment Variables
load_dotenv(find_dotenv(".env"))
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

# Authenticator
def is_authenticated(auth_header):
    return auth_header == f"Bearer {SECRET_TOKEN}"