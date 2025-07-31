#!/usr/bin/env python3

import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Testing logging...")
    print("Testing print statement...")
    logger.info("Logging test completed.")

if __name__ == "__main__":
    main()
