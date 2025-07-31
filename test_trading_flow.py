import sys
sys.path.append('.')

import os
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment
from config import MINIMUM_EDGE_CENTS, MAX_RISK_PER_TRADE

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


def test_trading_flow():
    """Test the complete trading flow to identify where issues might occur."""
    logger.info("Starting trading flow test...")
    
    try:
        # 1. Initialize client
        logger.info("1. Initializing Kalshi client...")
        client = load_kalshi_client('demo')
        logger.info("Client initialized successfully")
        
        # 2. Check balance
        logger.info("2. Checking portfolio balance...")
        balance_response = client.get_balance()
        portfolio_balance = balance_response.get('balance', 0)
        logger.info(f"Portfolio balance: ${portfolio_balance / 100:.2f}")
        
        # 3. Test place_order method accessibility
        logger.info("3. Testing place_order method accessibility...")
        if hasattr(client, 'place_order'):
            logger.info("place_order method is accessible")
        else:
            logger.error("place_order method is NOT accessible")
            return
        
        # 4. Try to get a sample market to test with
        logger.info("4. Fetching sample market data...")
        # Try to get all markets first
        all_markets = client.get('/trade-api/v2/markets')
        logger.info(f"Found {len(all_markets.get('markets', []))} markets")
        
        # Look for a Philadelphia weather market
        philly_markets = [m for m in all_markets.get('markets', []) 
                         if 'PHL' in m.get('ticker', '') and 'weather' in m.get('subtitle', '').lower()]
        
        if philly_markets:
            sample_market = philly_markets[0]
            ticker = sample_market['ticker']
            logger.info(f"Found Philadelphia weather market: {ticker}")
            
            # Get detailed market data
            market_data = client.get(f'/trade-api/v2/markets/{ticker}')
            market_info = market_data.get('market', {})
            
            logger.info(f"Market active: {market_info.get('active', False)}")
            logger.info(f"YES bid: {market_info.get('yes_bid', 'N/A')} cents")
            logger.info(f"NO bid: {market_info.get('no_bid', 'N/A')} cents")
            
        else:
            logger.warning("No Philadelphia weather markets found")
            
    except Exception as e:
        logger.error(f"Error in trading flow test: {e}", exc_info=True)
        return
    
    logger.info("Trading flow test completed.")

if __name__ == "__main__":
    test_trading_flow()
