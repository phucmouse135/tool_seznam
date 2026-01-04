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
    
    USER_AGENT_LIST = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    ]

    
    NUM_THREADS = 3
    BASE_PORT = 60000
    SEMAPHORE_LIMIT = 3
    RETRY_LIMIT = 5
    
    ONLINE_SIM_API_KEY = os.getenv("ONLINE_SIM_API_KEY")
    
    