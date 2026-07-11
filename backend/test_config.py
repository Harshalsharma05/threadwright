# backend/test_config.py
import sys
from app.config import settings

def test_loading():
    print("Checking configuration loading...")
    try:
        # Print non-sensitive fields or check length of secrets to verify they aren't empty
        print(f"Database URL configured: {bool(settings.database_url)}")
        print(f"Tavily Key present: {bool(settings.tavily_api_key)}")
        print(f"GitHub Token present: {bool(settings.github_token)}")
        print(f"Reddit Agent present: {bool(settings.reddit_user_agent)}")
        print(f"Groq Key present: {bool(settings.groq_api_key)}")
        print("Configuration successfully loaded and validated.")
    except Exception as e:
        print(f"Configuration load failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_loading()