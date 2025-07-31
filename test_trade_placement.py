#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment
from src.trading.trader import TradeExecutor

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

def test_trade_placement():
    """Test the trade placement functionality."""
    logger.info("Starting trade placement test...")
    
    try:
        # Initialize client
        client = load_kalshi_client('demo')
        
        # Get portfolio balance
        logger.info("Getting portfolio balance...")
        balance_response = client.get_balance()
        portfolio_balance = balance_response.get('balance', 1000000)  # Default to 10000 USD in cents
        logger.info(f"Portfolio balance: ${portfolio_balance / 100:.2f}")
        
        # Initialize trade executor
        trade_executor = TradeExecutor(client, portfolio_balance)
        
        # Test position sizing
        logger.info("Testing position sizing...")
        position_size = trade_executor.calculate_position_size(5, 0.6)  # 5 cents edge, 60% probability
        logger.info(f"Position size for 5 cents edge and 60% probability: {position_size} contracts")
        
        logger.info("Trade placement test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in trade placement test: {e}", exc_info=True)

if __name__ == "__main__":
    test_trade_placement()
