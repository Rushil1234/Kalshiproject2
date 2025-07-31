import sys
sys.path.append('.')

import os
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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


def test_simple_api_call():
    """Test a simple API call to check connectivity."""
    logger.info("Testing simple API call...")
    
    try:
        # Initialize client
        client = load_kalshi_client('demo')
        logger.info("Client initialized successfully")
        
        # Test a simple API call
        logger.info("Making simple API call...")
        response = client.get_exchange_status()
        logger.info(f"Exchange status: {response}")
        
    except Exception as e:
        logger.error(f"Error in simple API test: {e}", exc_info=True)
        return
    
    logger.info("Simple API test completed.")

if __name__ == "__main__":
    test_simple_api_call()
