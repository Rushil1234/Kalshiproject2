#!/usr/bin/env python3
"""
Test script to verify that the trading bot can place trades
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def test_trade_placement():
    """Test that we can place a trade through the Kalshi API"""
    from main import load_kalshi_client
    from src.trading.trader import TradeExecutor
    
    # Initialize client
    try:
        client = load_kalshi_client('demo')
        logger.info("Successfully initialized Kalshi client")
    except Exception as e:
        logger.error(f"Error initializing Kalshi client: {e}")
        return False
    
    # Get account balance
    try:
        balance_response = client.get_balance()
        portfolio_balance = balance_response['balance']
        logger.info(f"Account balance: {portfolio_balance} cents")
    except Exception as e:
        logger.error(f"Error getting account balance: {e}")
        return False
    
    # Initialize trade executor
    executor = TradeExecutor(client, portfolio_balance)
    
    # Test trade parameters (using a known ticker from our tests)
    test_ticker = 'KXHIGHPHIL-25AUG01-B76.5'
    test_side = 'no'
    test_count = 1
    test_price = 95  # 95 cents
    
    logger.info(f"Attempting to place test trade: {test_side} {test_count} contracts of {test_ticker} at {test_price} cents")
    
    # Place a test trade
    try:
        response = executor.place_trade(
            market_ticker=test_ticker,
            side=test_side,
            count=test_count,
            price=test_price
        )
        
        if response.get('success', False) or 'order' in response:
            logger.info(f"Successfully placed test trade: {response}")
            return True
        else:
            logger.error(f"Trade placement failed: {response}")
            return False
    except Exception as e:
        logger.error(f"Error placing test trade: {e}")
        return False


def main():
    """Run our trade placement test"""
    logger.info("Testing trade placement functionality...")
    
    success = test_trade_placement()
    
    if success:
        logger.info("Trade placement test completed successfully!")
        logger.info("The trading bot is now ready to place real trades.")
        return 0
    else:
        logger.error("Trade placement test failed.")
        logger.error("Please check the logs and verify your API credentials.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
