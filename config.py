from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # GraphQL API Configuration
    graphql_endpoint: str = "https://ly-budget-gql-dev-1075249966777.asia-east1.run.app/api/graphql"
    
    # Authentication (optional)
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    
    # API Settings
    api_timeout: int = 30
    api_max_retries: int = 3
    
    # GCS Settings
    gcs_bucket_name: Optional[str] = None
    gcs_credentials_path: Optional[str] = None
    gcs_output_prefix: str = "budget-statistics"  # Prefix for uploaded files


# Global settings instance
settings = Settings()
