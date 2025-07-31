#!/usr/bin/env python3
"""
Kalshi Weather Trading Bot - Main Controller
"""

import os
import argparse
import logging
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment
from config import TARGET_CITIES, NOAA_API_TOKEN_ENV_VAR

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_kalshi_client(environment):
    """Initialize and return a KalshiHttpClient instance."""
    load_dotenv()
    
    if environment == 'demo':
        key_id = os.getenv('DEMO_KEYID')
        key_file = os.getenv('DEMO_KEYFILE')
    else:  # prod
        key_id = os.getenv('PROD_KEYID')
        key_file = os.getenv('PROD_KEYFILE')
    
    if not key_id or not key_file:
        raise ValueError(f"Missing API credentials for {environment} environment. "
                         f"Please check your .env file.")
    
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


def train_model():
    """Train the weather prediction model."""
    logger.info("Starting model training...")
    # Import and run trainer
    from src.modeling import train_weather_model
    train_weather_model()
    logger.info("Model training completed.")


def run_backtest(client=None):
    """Run backtesting on historical data."""
    logger.info("Starting backtesting...")
    
    # Import required modules
    from src.backtesting.backtester import WalkForwardBacktester
    from src.data_collection.noaa_downloader import NOAADownloader
    from src.feature_engineering.feature_generator import WeatherFeatureGenerator
    import pandas as pd
    import os
    from datetime import datetime, timedelta
    
    try:
        # 1. Load historical data from existing files
        logger.info("Loading historical Philadelphia weather data from existing files...")
        
        # Find the largest features file (most data)
        import glob
        import os
        
        data_dir = "data"
        feature_files = glob.glob(os.path.join(data_dir, "philly_features_*.csv"))
        
        if not feature_files:
            logger.error("No feature files found. Please run backtesting with data download first.")
            return
        
        # Get the largest file by size
        largest_feature_file = max(feature_files, key=os.path.getsize)
        logger.info(f"Loading features from {largest_feature_file}")
        
        features_df = pd.read_csv(largest_feature_file)
        logger.info(f"Loaded {len(features_df)} records from {largest_feature_file}")
        
        # Extract weather data from features (assuming first few columns are weather data)
        weather_columns = ['date', 'max_temp', 'min_temp', 'precipitation']
        weather_df = features_df[weather_columns].copy() if all(col in features_df.columns for col in weather_columns) else features_df.copy()
        
        logger.info(f"Extracted weather data with {len(weather_df)} records")
        
        # 2. Generate features
        feature_generator = WeatherFeatureGenerator()
        features_df = feature_generator.generate_philly_features(weather_df)
        
        # 3. Load trained model and run walk-forward backtest
        # Look for the latest XGBoost model
        import glob
        model_files = glob.glob("models/philly_weather_xgb_target_high_temp_yes_*.joblib")
        if model_files:
            # Use the most recent model file
            model_files.sort(reverse=True)
            model_path = model_files[0]
            logger.info(f"Using model: {model_path}")
        else:
            model_path = "models/weather_model.pkl"  # Fallback to old model
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}. Please train the model first.")
            return
        
        backtester = WalkForwardBacktester(initial_capital=10000.0)
        results = backtester.run_walk_forward_backtest(
            features_df=features_df,
            model_path=model_path,
            train_window_days=365*3,  # 3 years
            test_window_days=90        # 90 days
        )
        
        logger.info("Backtesting completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during backtesting: {e}")
        raise


def run_trading(client=None):
    """Run live trading."""
    logger.info("Starting live trading...")
    # Import and run trader
    from src.trading.trader import run_trading_loop
    run_trading_loop(client)
    logger.info("Trading completed.")


def main():
    """Main entry point for the Kalshi weather trading bot."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Kalshi Weather Trading Bot')
    parser.add_argument('command', choices=['train', 'backtest', 'trade'], 
                        help='Command to execute')
    parser.add_argument('--env', choices=['demo', 'prod'], default='demo',
                        help='Environment to use (demo or prod)')
    
    args = parser.parse_args()
    
    # Load client for commands that need it
    if args.command in ['backtest', 'trade']:
        client = load_kalshi_client(args.env)
    
    # Execute the requested command
    if args.command == 'train':
        train_model()
    elif args.command == 'backtest':
        run_backtest(client)
    elif args.command == 'trade':
        run_trading(client)


if __name__ == "__main__":
    main()