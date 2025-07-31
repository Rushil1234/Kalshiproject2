#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_kalshi_client(environment):
    """Initialize and return a KalshiHttpClient instance."""
    logger.info("Loading environment variables...")
    load_dotenv()
    
    if environment == 'demo':
        key_id = os.getenv('DEMO_KEYID')
        key_file = os.getenv('DEMO_KEYFILE')
    else:  # prod
        key_id = os.getenv('PROD_KEYID')
        key_file = os.getenv('PROD_KEYFILE')
    
    logger.info(f"Key ID: {key_id}")
    logger.info(f"Key file: {key_file}")
    
    if not key_id or not key_file:
        raise ValueError(f"Missing API credentials for {environment} environment. Please check your .env file.")
    
    logger.info("Loading private key...")
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
    
    logger.info("Private key loaded successfully")
    
    env_enum = Environment.DEMO if environment == 'demo' else Environment.PROD
    
    logger.info("Creating KalshiHttpClient...")
    client = KalshiHttpClient(
        key_id=key_id,
        private_key=private_key,
        environment=env_enum
    )
    logger.info("KalshiHttpClient created successfully")
    
    return client

def main():
    logger.info("Starting client initialization test...")
    try:
        client = load_kalshi_client('demo')
        logger.info("Client initialization test completed successfully.")
    except Exception as e:
        logger.error(f"Error in client initialization test: {e}", exc_info=True)

if __name__ == "__main__":
    main()
