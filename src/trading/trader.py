"""
Live Trading Module for Weather Markets
"""

import logging
import time
import pandas as pd
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Local import
from config import MINIMUM_EDGE_CENTS, MAX_RISK_PER_TRADE
from src.data_collection.kalshi_scanner import KalshiWeatherScanner
from src.data_collection.noaa_downloader import NOAADownloader
from src.feature_engineering.feature_generator import WeatherFeatureGenerator
from src.modeling.predictor import WeatherPredictor

logger = logging.getLogger(__name__)


def run_trading_loop(client=None):
    """Run the live trading loop with risk management and edge logic."""
    logger.info("Starting live trading loop")
    
    if client is None:
        logger.error("Kalshi client is required for trading")
        return
    
    # Initialize trade executor
    try:
        # Get current portfolio balance
        balance_response = client.get_balance()
        portfolio_balance = balance_response.get('balance', 1000000)  # Default to 10000 USD in cents
        logger.info(f"Current portfolio balance: ${portfolio_balance / 100:.2f}")
        
        trade_executor = TradeExecutor(client, portfolio_balance)
    except Exception as e:
        logger.error(f"Failed to initialize trade executor: {e}")
        return
    
    # Main trading loop
    iteration = 0
    max_iterations = 1000  # Prevent infinite loop in demo
    
    # Initialize market scanner
    scanner = KalshiWeatherScanner(client)
    
    while iteration < max_iterations:
        try:
            logger.info(f"Trading iteration {iteration + 1}")
            
            # 1. Scan for Philadelphia weather markets
            markets = scanner.scan_weather_markets()
            if not markets:
                logger.info("No markets found for trading")
                time.sleep(60)  # Wait before next iteration
                iteration += 1
                continue
            
            # 2. For each market, get latest weather data and make predictions
            for market in markets:
                ticker = market['ticker']
                logger.info(f"Analyzing market: {ticker}")
                
                # 3. Get latest weather data for Philadelphia
                noaa_downloader = NOAADownloader()
                # For live trading, we'll use recent data (last 7 days)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                weather_data = noaa_downloader.download_philly_historical_data(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                if weather_data is None or weather_data.empty:
                    logger.warning(f"Could not get weather data for {ticker}")
                    continue
                
                # 4. Generate features
                feature_generator = WeatherFeatureGenerator()
                features = feature_generator.generate_philly_features(weather_data)
                
                # 5. Get model prediction
                predictor = WeatherPredictor()
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
                
                if os.path.exists(model_path):
                    predictor.load_model(model_path)
                    prediction_prob = predictor.predict(features)
                else:
                    logger.warning(f"Model file {model_path} not found. Using placeholder prediction.")
                    # Use a placeholder prediction if no model is available
                    prediction_prob = 0.5  # 50% probability as placeholder
                
                # 6. Calculate fair value
                fair_value = prediction_prob * 100  # Convert to cents
                
                # 7. Check market prices
                try:
                    market_data = client.get(f'/trade-api/v2/markets/{ticker}')
                    
                    # Log the full market data for debugging
                    logger.debug(f"Full market data for {ticker}: {market_data}")
                    
                    # Check if market data is valid
                    if 'market' not in market_data:
                        logger.warning(f"Invalid market data structure for {ticker}: {market_data}")
                        continue
                        
                    market_info = market_data['market']
                    
                    # Check if market is active
                    if not market_info.get('active', False):
                        logger.info(f"Market {ticker} is not active, skipping")
                        continue
                    
                    # Get prices, with defaults if not available
                    yes_price = market_info.get('yes_bid', 0)
                    no_price = market_info.get('no_bid', 100)
                    
                    # Convert numpy values to scalar for logging
                    yes_price_scalar = yes_price.item() if hasattr(yes_price, 'item') else yes_price
                    no_price_scalar = no_price.item() if hasattr(no_price, 'item') else no_price
                    
                    logger.info(f"Market {ticker} - YES bid: {yes_price_scalar} cents, NO bid: {no_price_scalar} cents")
                    logger.info(f"Fair value: {fair_value:.2f} cents")
                    
                    # 8. Calculate edges
                    yes_edge = fair_value - yes_price_scalar
                    no_edge = (100 - fair_value) - no_price_scalar
                    
                    logger.info(f"YES edge: {yes_edge:.2f} cents, NO edge: {no_edge:.2f} cents")
                    
                    # 9. Check for trading opportunities
                    # Apply certainty rule: only trade if prediction is confident enough
                    certainty_threshold = 0.55  # Lowered from 0.7 to make more trades
                    
                    # Log detailed trading conditions
                    logger.info(f"Trading conditions for {ticker}:")
                    logger.info(f"  YES edge: {yes_edge:.2f} cents (minimum: {MINIMUM_EDGE_CENTS})")
                    logger.info(f"  NO edge: {no_edge:.2f} cents (minimum: {MINIMUM_EDGE_CENTS})")
                    logger.info(f"  Prediction probability: {prediction_prob:.3f} (threshold: {certainty_threshold})")
                    
                    # Always attempt to trade if there's any edge, even with low certainty for demo purposes
                    if yes_edge >= 3:  # Lowered minimum edge to 3 cents for demo
                        # Place YES trade
                        position_size = trade_executor.calculate_position_size(yes_edge, prediction_prob)
                        # Even if position size is small, place a minimum trade for demo
                        if position_size == 0 and yes_edge >= 3:
                            position_size = 10  # Minimum position size for demo
                        if position_size > 0:
                            logger.info(f"Placing YES trade on {ticker} with {position_size} contracts at {yes_price} cents")
                            trade_executor.place_trade(ticker, 'yes', position_size, yes_price)
                    elif no_edge >= 3:  # Lowered minimum edge to 3 cents for demo
                        # Place NO trade
                        position_size = trade_executor.calculate_position_size(no_edge, 1 - prediction_prob)
                        # Even if position size is small, place a minimum trade for demo
                        if position_size == 0 and no_edge >= 3:
                            position_size = 10  # Minimum position size for demo
                        if position_size > 0:
                            logger.info(f"Placing NO trade on {ticker} with {position_size} contracts at {no_price} cents")
                            trade_executor.place_trade(ticker, 'no', position_size, no_price)
                    else:
                        logger.info(f"No trading opportunity for {ticker} (insufficient edge)")
                
                except Exception as e:
                    logger.error(f"Error getting market data for {ticker}: {e}")
                    continue
            
            # Wait before next iteration
            logger.info("Waiting 5 minutes before next trading iteration")
            time.sleep(300)  # 5 minutes
            iteration += 1
            
        except KeyboardInterrupt:
            logger.info("Trading loop interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(60)  # Wait before retrying
            iteration += 1
            continue
    
    logger.info("Trading loop completed")


class TradeExecutor:
    """Executor for placing trades on Kalshi."""
    
    def __init__(self, client, portfolio_balance: float):
        """
        Initialize the trade executor.
        
        Args:
            client: KalshiHttpClient instance
            portfolio_balance: Current portfolio balance in cents
        """
        self.client = client
        self.portfolio_balance = portfolio_balance
    
    def calculate_position_size(self, edge_cents: float, probability: float) -> int:
        """
        Calculate position size using a simplified Kelly Criterion.
        
        Args:
            edge_cents: Edge in cents (fair_value - market_price)
            probability: Model's predicted probability
            
        Returns:
            Position size in contracts
        """
        # Simplified Kelly Criterion: f = (bp - q) / b
        # where b = odds, p = win probability, q = loss probability
        
        # For demo purposes, allow trading with lower edge
        minimum_edge_for_trading = 3  # cents
        
        if edge_cents < minimum_edge_for_trading:
            return 0  # Don't trade if edge is too small
        
        # Convert edge to probability terms
        edge_probability = edge_cents / 100.0
        
        # Odds (simplified - in practice, you'd use the actual market prices)
        odds = 1.0
        
        # Kelly fraction
        kelly_fraction = (odds * probability - (1 - probability)) / odds
        
        # Apply risk limits
        kelly_fraction = max(0, min(kelly_fraction, MAX_RISK_PER_TRADE))
        
        # Calculate position size in dollars
        position_value = self.portfolio_balance * kelly_fraction
        
        # Convert to number of contracts (assuming $1 per contract)
        position_size = int(position_value / 100)  # Convert cents to dollars
        
        # For demo purposes, ensure a minimum position size if there's any edge
        if position_size == 0 and edge_cents >= minimum_edge_for_trading:
            return 10  # Minimum position size for demo
        
        return max(0, position_size)
    
    def place_trade(self, market_ticker: str, side: str, count: int, price: int) -> Dict[str, Any]:
        """
        Place a trade on Kalshi.
        
        Args:
            market_ticker: Market ticker symbol
            side: 'yes' or 'no'
            count: Number of contracts
            price: Price in cents per contract
            
        Returns:
            Trade response
        """
        logger.info(f"Placing trade: {side} {count} contracts of {market_ticker} at {price} cents")
        
        try:
            # Use the Kalshi API to place the order
            response = self.client.place_order(
                market_ticker=market_ticker,
                yes_or_no=side,
                quantity=count,
                price=price
            )
            
            logger.info(f"Trade placed successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            return {"success": False, "error": str(e)}
