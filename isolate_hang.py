#!/usr/bin/env python3

import os
import logging
import time
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting hang isolation test...")
    
    try:
        # Step 1: Load environment variables
        logger.info("Step 1: Loading environment variables...")
        load_dotenv()
        logger.info("Environment variables loaded")
        
        # Step 2: Get credentials
        logger.info("Step 2: Getting credentials...")
        key_id = os.getenv('DEMO_KEYID')
        key_file = os.getenv('DEMO_KEYFILE')
        logger.info(f"Key ID: {key_id}")
        logger.info(f"Key file: {key_file}")
        
        # Step 3: Load private key
        logger.info("Step 3: Loading private key...")
        with open(key_file, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        logger.info("Private key loaded")
        
        # Step 4: Create client
        logger.info("Step 4: Creating KalshiHttpClient...")
        start_time = time.time()
        client = KalshiHttpClient(
            key_id=key_id,
            private_key=private_key,
            environment=Environment.DEMO
        )
        end_time = time.time()
        logger.info(f"KalshiHttpClient created in {end_time - start_time:.2f} seconds")
        
        # Step 5: Test first API call
        logger.info("Step 5: Testing first API call...")
        start_time = time.time()
        try:
            status = client.get_exchange_status()
            end_time = time.time()
            logger.info(f"First API call completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Exchange status: {status}")
        except Exception as e:
            end_time = time.time()
            logger.error(f"First API call failed after {end_time - start_time:.2f} seconds: {e}")
            return
        
        logger.info("Hang isolation test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in hang isolation test: {e}", exc_info=True)

if __name__ == "__main__":
    main()
