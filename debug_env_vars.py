#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting environment variable debug...")
    
    # Load environment variables
    logger.info("Loading .env file...")
    load_dotenv()
    
    # Check environment variables
    logger.info("Checking environment variables...")
    demo_keyid = os.getenv('DEMO_KEYID')
    demo_keyfile = os.getenv('DEMO_KEYFILE')
    noaa_token = os.getenv('NOAA_API_TOKEN')
    
    logger.info(f"DEMO_KEYID: {demo_keyid}")
    logger.info(f"DEMO_KEYFILE: {demo_keyfile}")
    logger.info(f"NOAA_API_TOKEN: {noaa_token}")
    
    # Check if files exist
    if demo_keyfile:
        if os.path.exists(demo_keyfile):
            logger.info(f"Key file {demo_keyfile} exists")
            # Check file size
            size = os.path.getsize(demo_keyfile)
            logger.info(f"Key file size: {size} bytes")
        else:
            logger.error(f"Key file {demo_keyfile} does not exist")
    
    logger.info("Environment variable debug completed.")

if __name__ == "__main__":
    main()
