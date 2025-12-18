import os
from dotenv import load_dotenv

load_dotenv()

print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRES_AT = int(os.getenv("ACCESS_TOKEN_EXPIRES_AT", 30))
DATABASE_URL = os.getenv("DATABASE_URL")
