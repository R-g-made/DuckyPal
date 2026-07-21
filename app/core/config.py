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
    
    # Postgres components
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "duckypal")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "utyapal_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET")
    
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return self.SQLITE_URL
        
        # Build Postgres URL from components to avoid interpolation issues in .env
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Proxy settings
    PROXY_URL: str = os.getenv("PROXY_URL")  # e.g., http://proxy.server:3128
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
