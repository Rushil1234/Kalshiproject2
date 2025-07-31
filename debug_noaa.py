#!/usr/bin/env python3
"""
Debug script to investigate NOAA data fetching issues
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_noaa.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def debug_noaa_fetch():
    """Debug the NOAA data fetching process"""
    from src.data_collection.noaa_downloader import NOAADownloader
    
    try:
        downloader = NOAADownloader()
        logger.info("Successfully initialized NOAA downloader")
        
        # Test with a date range that should have data
        # Using a date range from a few days ago to ensure data exists
        start_date = '2025-07-25'
        end_date = '2025-07-31'
        
        logger.info(f"Attempting to download data for {start_date} to {end_date}")
        df = downloader.download_philly_historical_data(start_date, end_date)
        
        if df is not None:
            logger.info(f"Successfully downloaded NOAA data with {len(df)} records")
            logger.info(f"Data columns: {df.columns.tolist()}")
            logger.info(f"First few rows:\n{df.head()}")
            return True
        else:
            logger.error("NOAA data download returned None")
            return False
    except Exception as e:
        logger.error(f"Error testing NOAA downloader: {e}", exc_info=True)
        return False


def main():
    """Run our debug test"""
    logger.info("Debugging NOAA data fetching...")
    
    success = debug_noaa_fetch()
    
    if success:
        logger.info("NOAA debug test completed successfully!")
        return 0
    else:
        logger.error("NOAA debug test failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
