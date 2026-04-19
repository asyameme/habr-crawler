import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MAX_DEPTH = int(os.getenv("MAX_DEPTH", "2"))
HABR_RATE_LIMIT_SEC = int(os.getenv("HABR_RATE_LIMIT_SEC", "10"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "1000"))

