#!/usr/bin/env python3
"""
Test script to verify our fixes for the Kalshi trading bot
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_fixes.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def test_market_data_fetch():
    """Test that we can fetch market data with the corrected endpoint"""
    from main import load_kalshi_client
    
    # Initialize client
    try:
        client = load_kalshi_client('demo')
        logger.info("Successfully initialized Kalshi client")
    except Exception as e:
        logger.error(f"Error initializing Kalshi client: {e}")
        return False
    
    # Try to fetch a market (using a known ticker from the logs)
    try:
        market_data = client.get('/trade-api/v2/markets/KXHIGHPHIL-25AUG01-B76.5')
        logger.info(f"Successfully fetched market data: {market_data}")
        return True
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return False


def test_noaa_downloader():
    """Test that the NOAA downloader handles timeouts better"""
    from src.data_collection.noaa_downloader import NOAADownloader
    
    try:
        downloader = NOAADownloader()
        # Test with a short date range to minimize timeout risk
        df = downloader.download_philly_historical_data('2025-07-30', '2025-07-31')
        if df is not None:
            logger.info(f"Successfully downloaded NOAA data with {len(df)} records")
            return True
        else:
            logger.warning("NOAA data download returned None")
            return False
    except Exception as e:
        logger.error(f"Error testing NOAA downloader: {e}")
        return False


def main():
    """Run our tests"""
    logger.info("Testing fixes for Kalshi trading bot...")
    
    # Test market data fetch
    logger.info("Testing market data fetch...")
    market_success = test_market_data_fetch()
    
    # Test NOAA downloader
    logger.info("Testing NOAA downloader...")
    noaa_success = test_noaa_downloader()
    
    if market_success and noaa_success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
