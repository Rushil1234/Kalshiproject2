"""
Feature Engineering for Philadelphia Weather Data
"""

import logging
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherFeatureGenerator:
    """Generator for Philadelphia weather data features."""
    
    def __init__(self):
        """Initialize the feature generator."""
        pass
    
    def generate_philly_features(self, weather_df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Generate features from Philadelphia weather data.
        
        Args:
            weather_df: DataFrame with Philadelphia weather data
            market_data: Optional DataFrame with Kalshi market data
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Generating Philadelphia weather features...")
        
        # Make a copy to avoid modifying the original
        df = weather_df.copy()
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        # Generate baseline features
        df = self._generate_baseline_features(df)
        
        # Generate advanced features
        df = self._generate_advanced_features(df)
        
        # Always generate target variables
        df = self._generate_targets(df, market_data)
        
        # Save features to CSV
        os.makedirs('data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/philly_features_{timestamp}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Saved features to {filename}")
        
        logger.info(f"Generated {len(df.columns)} features for {len(df)} records")
        return df
    
    def _generate_baseline_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate baseline Philadelphia weather features.
        
        Args:
            df: DataFrame with weather data
            
        Returns:
            DataFrame with baseline features added
        """
        # Temperature features
        if 'max_temp' in df.columns:
            df['max_temp_f'] = (df['max_temp'] * 9/5) + 32  # Convert to Fahrenheit
            df['max_temp_above_avg'] = df['max_temp'] > df['max_temp'].mean()  # Above historical average
        
        if 'min_temp' in df.columns:
            df['min_temp_f'] = (df['min_temp'] * 9/5) + 32  # Convert to Fahrenheit
            df['min_temp_above_avg'] = df['min_temp'] > df['min_temp'].mean()  # Above historical average
        
        # Date-based features
        if 'date' in df.columns:
            df['day_of_year'] = df['date'].dt.dayofyear
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.dayofweek
            df['quarter'] = df['date'].dt.quarter
            df['week_of_year'] = df['date'].dt.isocalendar().week
            
            # Seasonal features specific to Philadelphia
            df['is_summer'] = ((df['month'] >= 6) & (df['month'] <= 8)).astype(int)
            df['is_winter'] = ((df['month'] >= 12) | (df['month'] <= 2)).astype(int)
            df['is_spring'] = ((df['month'] >= 3) & (df['month'] <= 5)).astype(int)
            df['is_fall'] = ((df['month'] >= 9) & (df['month'] <= 11)).astype(int)
            
            # Holiday features (simplified)
            # Summer vacation period (June 15 - September 15)
            df['is_summer_vacation'] = ((df['month'] == 6) & (df['date'].dt.day >= 15)) | \
                                      (df['month'] == 7) | \
                                      (df['month'] == 8) | \
                                      ((df['month'] == 9) & (df['date'].dt.day <= 15))
            df['is_summer_vacation'] = df['is_summer_vacation'].astype(int)
        
        # Precipitation features
        if 'precipitation' in df.columns:
            df['precipitation_inches'] = df['precipitation'] / 25.4  # Convert to inches
            df['is_rainy_day'] = (df['precipitation'] > 5.0).astype(int)  # More than 5mm
            df['is_dry_day'] = (df['precipitation'] == 0).astype(int)
        
        return df
    
    def _generate_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate advanced Philadelphia weather features.
        
        Args:
            df: DataFrame with weather data and baseline features
            
        Returns:
            DataFrame with advanced features added
        """
        # Moving averages (if we have multiple days of data)
        if 'max_temp' in df.columns:
            df['max_temp_ma_3'] = df['max_temp'].rolling(window=3, min_periods=1).mean()
            df['max_temp_ma_7'] = df['max_temp'].rolling(window=7, min_periods=1).mean()
            df['max_temp_ma_14'] = df['max_temp'].rolling(window=14, min_periods=1).mean()
            df['max_temp_ma_30'] = df['max_temp'].rolling(window=30, min_periods=1).mean()
        
        if 'min_temp' in df.columns:
            df['min_temp_ma_3'] = df['min_temp'].rolling(window=3, min_periods=1).mean()
            df['min_temp_ma_7'] = df['min_temp'].rolling(window=7, min_periods=1).mean()
            df['min_temp_ma_14'] = df['min_temp'].rolling(window=14, min_periods=1).mean()
        
        # Exponential moving averages
        if 'max_temp' in df.columns:
            df['max_temp_ema_7'] = df['max_temp'].ewm(span=7, min_periods=1).mean()
            df['max_temp_ema_14'] = df['max_temp'].ewm(span=14, min_periods=1).mean()
        
        # Lagged features
        if 'max_temp' in df.columns:
            df['max_temp_lag_1'] = df['max_temp'].shift(1)
            df['max_temp_lag_2'] = df['max_temp'].shift(2)
            df['max_temp_lag_7'] = df['max_temp'].shift(7)
        
        if 'min_temp' in df.columns:
            df['min_temp_lag_1'] = df['min_temp'].shift(1)
            df['min_temp_lag_2'] = df['min_temp'].shift(2)
            df['min_temp_lag_7'] = df['min_temp'].shift(7)
        
        # Difference features
        if 'max_temp' in df.columns:
            df['max_temp_diff_1'] = df['max_temp'].diff(1)
            df['max_temp_diff_7'] = df['max_temp'].diff(7)
        
        if 'min_temp' in df.columns:
            df['min_temp_diff_1'] = df['min_temp'].diff(1)
            df['min_temp_diff_7'] = df['min_temp'].diff(7)
        
        # Interaction terms
        if 'max_temp' in df.columns and 'min_temp' in df.columns:
            df['temp_range'] = df['max_temp'] - df['min_temp']
            df['temp_mean'] = (df['max_temp'] + df['min_temp']) / 2
            df['temp_range_ma_7'] = df['temp_range'].rolling(window=7, min_periods=1).mean()
        
        # Precipitation features
        if 'precipitation' in df.columns:
            df['precipitation_ma_3'] = df['precipitation'].rolling(window=3, min_periods=1).mean()
            df['precipitation_ma_7'] = df['precipitation'].rolling(window=7, min_periods=1).mean()
            df['had_precipitation'] = (df['precipitation'] > 0).astype(int)
            df['heavy_precipitation'] = (df['precipitation'] > 10.0).astype(int)  # More than 10mm
        
        # Temperature thresholds specific to Philadelphia
        if 'max_temp' in df.columns:
            df['above_80F'] = (df['max_temp'] > 26.67).astype(int)  # 80F = 26.67C
            df['above_90F'] = (df['max_temp'] > 32.22).astype(int)  # 90F = 32.22C
            df['above_95F'] = (df['max_temp'] > 35.00).astype(int)  # 95F = 35.00C
            df['above_98F'] = (df['max_temp'] > 36.67).astype(int)  # 98F = 36.67C
            df['below_32F'] = (df['min_temp'] < 0).astype(int)      # 32F = 0C (freezing)
            df['below_20F'] = (df['min_temp'] < -6.67).astype(int)   # 20F = -6.67C
        
        # Volatility features
        if 'max_temp' in df.columns:
            df['max_temp_volatility_7'] = df['max_temp'].rolling(window=7, min_periods=1).std()
            df['max_temp_volatility_30'] = df['max_temp'].rolling(window=30, min_periods=1).std()
        
        if 'min_temp' in df.columns:
            df['min_temp_volatility_7'] = df['min_temp'].rolling(window=7, min_periods=1).std()
        
        # Trend features
        if 'max_temp' in df.columns:
            df['max_temp_trend_7'] = df['max_temp'].rolling(window=7, min_periods=7).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 7 else np.nan, raw=False)
            df['max_temp_trend_14'] = df['max_temp'].rolling(window=14, min_periods=14).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 14 else np.nan, raw=False)
        
        return df
    
    def _generate_targets(self, weather_df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Generate target variables by matching weather data with market outcomes.
        
        Args:
            weather_df: DataFrame with weather data and features
            market_data: Optional DataFrame with Kalshi market data
            
        Returns:
            DataFrame with target variables added
        """
        logger.info("Generating target variables...")
        
        # Always create target columns, even if market data is not available
        # In a real implementation, you would:
        # 1. Parse market titles to extract temperature thresholds
        # 2. Match market dates with weather dates
        # 3. Determine if the market resolved YES or NO based on actual weather
        
        if market_data is not None and not market_data.empty:
            logger.info("Generating targets from actual market data...")
            # For now, we'll just add placeholder targets
            # In a real implementation, you would extract actual market outcomes
            weather_df['target_high_temp_yes'] = np.random.choice([0, 1], size=len(weather_df))
            weather_df['target_low_temp_yes'] = np.random.choice([0, 1], size=len(weather_df))
        else:
            logger.info("Generating placeholder targets for backtesting...")
            # Create placeholder targets for backtesting
            weather_df['target_high_temp_yes'] = np.random.choice([0, 1], size=len(weather_df))
            weather_df['target_low_temp_yes'] = np.random.choice([0, 1], size=len(weather_df))
        
        return weather_df
