import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "UtyaPal"
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Database selection logic
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "True").lower() == "true"
    SQLITE_URL: str = os.getenv("SQLITE_URL", "sqlite:///./sql_app.db")
    POSTGRES_URL: str = os.getenv("POSTGRES_URL")
    
    @property
    def DATABASE_URL(self) -> str:
        return self.SQLITE_URL if self.USE_SQLITE else self.POSTGRES_URL
    
    # Proxy settings
    PROXY_URL: str = os.getenv("PROXY_URL")  # e.g., http://proxy.server:3128
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
