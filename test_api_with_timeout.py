import sys
sys.path.append('.')

import os
import logging
import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_kalshi_client(environment='demo'):
    """Initialize and return a KalshiHttpClient instance."""
    load_dotenv()
    
    if environment == 'demo':
        key_id = os.getenv('DEMO_KEYID')
        key_file = os.getenv('DEMO_KEYFILE')
    else:  # prod
        key_id = os.getenv('PROD_KEYID')
        key_file = os.getenv('PROD_KEYFILE')
    
    if not key_id or not key_file:
        raise ValueError(f"Missing API credentials for {environment} environment. Please check your .env file.")
    
    try:
        with open(key_file, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {key_file}")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")
    
    env_enum = Environment.DEMO if environment == 'demo' else Environment.PROD
    
    return KalshiHttpClient(
        key_id=key_id,
        private_key=private_key,
        environment=env_enum
    )


def test_api_with_timeout():
    """Test API calls with explicit timeout handling."""
    logger.info("Testing API calls with timeout handling...")
    
    try:
        # Initialize client
        client = load_kalshi_client('demo')
        logger.info("Client initialized successfully")
        
        # Test a simple API call with timeout
        logger.info("Making API call with timeout...")
        
        # Manually make a request with timeout to test
        host = client.HTTP_BASE_URL
        path = "/trade-api/v2/exchange/status"
        headers = client.request_headers("GET", path)
        
        logger.info(f"Making request to: {host + path}")
        logger.info(f"Headers: {headers}")
        
        try:
            response = requests.get(
                host + path,
                headers=headers,
                timeout=10  # 10 second timeout
            )
            response.raise_for_status()
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response data: {response.json()}")
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return
        
    except Exception as e:
        logger.error(f"Error in API timeout test: {e}", exc_info=True)
        return
    
    logger.info("API timeout test completed.")

if __name__ == "__main__":
    test_api_with_timeout()
