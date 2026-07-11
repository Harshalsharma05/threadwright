from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    tavily_api_key: str
    github_token: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    groq_api_key: str
    anthropic_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()