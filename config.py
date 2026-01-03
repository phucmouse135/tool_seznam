import os 

from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Configuration settings
class Config:
    PROXY_API_BASE = "http://127.0.0.1:10101/api/proxy"
    PROXY_LIST = [
        {"server": "socks5://127.0.0.1:60000"},
        {"server": "socks5://127.0.0.1:60001"},
        {"server": "socks5://127.0.0.1:60002"}
    ]
    TARGET_CONFIG = {
    "timezone": "Europe/Prague",
    "locale": "cs-CZ",
    "geolocation": {"latitude": 50.0755, "longitude": 14.4378}
    }

    
    NUM_THREADS = 3
    BASE_PORT = 60000
    SEMAPHORE_LIMIT = 3
    RETRY_LIMIT = 3
    
    ONLINE_SIM_API_KEY = os.getenv("ONLINE_SIM_API_KEY")
    
    