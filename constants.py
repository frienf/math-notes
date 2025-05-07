from dotenv import load_dotenv
import os
load_dotenv()

SERVER_URL = 'localhost'
PORT = '8900'
ENV = 'dev'

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in the environment variables.")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", 10_000_000))
ALLOWED_IMAGE_FORMATS = tuple(os.getenv("ALLOWED_IMAGE_FORMATS", "PNG,JPEG").split(","))