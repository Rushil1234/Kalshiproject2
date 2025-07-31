"""
Kalshi Market Scanner for Weather Markets (Philadelphia Only)
"""

import logging
import pandas as pd
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KalshiWeatherScanner:
    """Scanner for Kalshi weather markets focused on Philadelphia."""
    
    def __init__(self, client):
        """
        Initialize the scanner with a Kalshi HTTP client.
        
        Args:
            client: KalshiHttpClient instance
        """
        self.client = client
    
    def scan_weather_markets(self) -> List[Dict[str, Any]]:
        """
        Scan for all active weather markets on Kalshi, filtering for Philadelphia only.
        
        Returns:
            List of Philadelphia weather market data dictionaries
        """
        logger.info("Scanning for active Philadelphia weather markets...")
        
        # Get all markets (implementing pagination)
        all_markets = []
        limit = 100
        cursor = None
        
        while True:
            params = {"status": "open", "limit": limit}
            if cursor:
                params["cursor"] = cursor
                
            try:
                markets_response = self.client.get("/trade-api/v2/markets", params=params)
            except Exception as e:
                logger.error(f"Error fetching markets: {e}")
                break
            
            markets = markets_response.get('markets', [])
            all_markets.extend(markets)
            
            # Check if there are more markets
            cursor = markets_response.get('cursor')
            if not cursor or len(markets) < limit:
                break
        
        philly_weather_markets = []
        
        # Filter for Philadelphia weather markets
        for market in all_markets:
            if self._is_philly_weather_market(market):
                parsed_market = self._parse_weather_market(market)
                if parsed_market:
                    philly_weather_markets.append(parsed_market)
        
        logger.info(f"Found {len(philly_weather_markets)} active Philadelphia weather markets")
        
        # Save to CSV for later analysis
        if philly_weather_markets:
            os.makedirs('data', exist_ok=True)
            df = pd.DataFrame(philly_weather_markets)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/kalshi_philly_markets_{timestamp}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"Saved Philadelphia market data to {filename}")
        
        return philly_weather_markets
    
    def _is_philly_weather_market(self, market: Dict[str, Any]) -> bool:
        """
        Determine if a market is a Philadelphia weather market.
        
        Args:
            market: Market data dictionary
            
        Returns:
            True if market is a Philadelphia weather market
        """
        # Check for Philadelphia-specific markets
        title = market.get('title', '').lower()
        
        # Check for Philadelphia mentions
        philly_keywords = ['philadelphia', 'philly', 'phl', 'philidelphia']  # Including common misspellings
        
        has_philly_keywords = any(keyword in title for keyword in philly_keywords)
        
        # Also check for weather-related keywords
        weather_keywords = ['weather', 'temperature', 'temp', 'high', 'low', 'precipitation', 'rain']
        has_weather_keywords = any(keyword in title for keyword in weather_keywords)
        
        return has_philly_keywords and has_weather_keywords
    
    def _parse_weather_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Philadelphia weather market into standardized format.
        
        Args:
            market: Market data dictionary
            
        Returns:
            Parsed market data or None if invalid
        """
        try:
            # Extract key information
            ticker = market.get('ticker', '')
            title = market.get('title', '')
            category = market.get('category', '')
            
            # Parse city (always Philadelphia for our filtered markets)
            city = "Philadelphia"
            
            # Parse weather variable from title
            weather_var = self._extract_weather_variable(title)
            
            # Extract date information
            start_date = market.get('start_date', '')
            end_date = market.get('end_date', '')
            
            # Extract contract details
            yes_price = market.get('yes_price', 0)
            no_price = market.get('no_price', 0)
            
            # Extract outcome prices if available
            outcomes = market.get('outcomes', [])
            outcome_prices = {}
            for outcome in outcomes:
                outcome_ticker = outcome.get('ticker', '')
                outcome_price = outcome.get('price', 0)
                outcome_prices[outcome_ticker] = outcome_price
            
            # Extract additional metadata
            volume = market.get('volume', 0)
            open_interest = market.get('open_interest', 0)
            
            # Extract temperature range if available
            temp_range = self._extract_temp_range(title)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'title': title,
                'category': category,
                'city': city,
                'weather_variable': weather_var,
                'temp_range': temp_range,
                'start_date': start_date,
                'end_date': end_date,
                'yes_price': yes_price,
                'no_price': no_price,
                'outcome_prices': json.dumps(outcome_prices),
                'volume': volume,
                'open_interest': open_interest,
                'raw_data': json.dumps(market)  # Keep raw data for reference
            }
        except Exception as e:
            logger.warning(f"Failed to parse market {market.get('ticker', 'unknown')}: {e}")
            return None
    
    def _extract_weather_variable(self, title: str) -> str:
        """
        Extract weather variable from market title.
        
        Args:
            title: Market title
            
        Returns:
            Weather variable description
        """
        title_lower = title.lower()
        
        if 'high' in title_lower and ('temp' in title_lower or 'temperature' in title_lower):
            return 'high_temperature'
        elif 'low' in title_lower and ('temp' in title_lower or 'temperature' in title_lower):
            return 'low_temperature'
        elif 'precipitation' in title_lower or 'rain' in title_lower:
            return 'precipitation'
        else:
            return 'unknown'
    
    def _extract_temp_range(self, title: str) -> str:
        """
        Extract temperature range from market title.
        
        Args:
            title: Market title
            
        Returns:
            Temperature range string
        """
        # This is a simplified implementation
        # In practice, you'd want a more robust regex-based parser
        return title
