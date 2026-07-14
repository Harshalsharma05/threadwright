# Save this temporarily as backend/test_dns.py
import socket
from urllib.parse import urlparse
from app.config import settings

try:
    # Extract host from the DATABASE_URL
    url = settings.database_url
    # Strip the asyncpg dialect prefix if present so urlparse works cleanly
    clean_url = url.replace("+asyncpg", "")
    parsed = urlparse(clean_url)
    host = parsed.hostname
    
    print(f"Attempting to resolve host: {host}")
    ip = socket.gethostbyname(host)
    print(f"Success! Resolved {host} to {ip}")
except Exception as e:
    print(f"DNS Resolution failed: {e}")