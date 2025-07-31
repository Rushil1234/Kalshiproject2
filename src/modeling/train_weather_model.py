"""
Function to train the weather model for Philadelphia.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from src.modeling.trainer import WeatherModelTrainer
from src.data_collection.noaa_downloader import NOAADownloader
from src.feature_engineering.feature_generator import WeatherFeatureGenerator

logger = logging.getLogger(__name__)

def train_weather_model():
    """Train the weather prediction model for Philadelphia."""
    logger.info("Starting weather model training for Philadelphia...")
    
    # Initialize components
    downloader = NOAADownloader()
    feature_generator = WeatherFeatureGenerator()
    trainer = WeatherModelTrainer()
    
    # Use existing NOAA data files
    logger.info("Loading historical Philadelphia weather data from existing files...")
    
    try:
        # Load all existing NOAA data files
        import glob
        noaa_files = glob.glob("data/noaa_philly_*.csv")
        if not noaa_files:
            logger.error("No existing NOAA data files found")
            return
            
        # Load and combine all NOAA data files
        weather_data_list = []
        for file in noaa_files:
            try:
                df = pd.read_csv(file)
                weather_data_list.append(df)
            except Exception as e:
                logger.warning(f"Failed to load {file}: {str(e)}")
                continue
                
        if not weather_data_list:
            logger.error("Failed to load any NOAA data files")
            return
            
        weather_data = pd.concat(weather_data_list, ignore_index=True)
        logger.info(f"Loaded {len(weather_data)} records from {len(weather_data_list)} NOAA data files")
        
        if weather_data is None or weather_data.empty:
            logger.error("Failed to download Philadelphia weather data")
            return
            
        logger.info(f"Downloaded {len(weather_data)} records of Philadelphia weather data")
        
        # Generate features
        logger.info("Generating Philadelphia weather features...")
        features = feature_generator.generate_philly_features(weather_data)
        
        if features is None or features.empty:
            logger.error("Failed to generate features")
            return
            
        logger.info(f"Generated {len(features)} records with {len(features.columns)-1} features (excluding date)")
        
        # Train model for high temperature prediction
        logger.info("Training model for high temperature prediction...")
        target_column = "target_high_temp_yes"
        
        if target_column not in features.columns:
            logger.error(f"Target column '{target_column}' not found in features")
            return
            
        model, metrics = trainer.train_model(features, target_column)
        
        # Save the trained model
        os.makedirs('models', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"models/philly_weather_xgb_{target_column}_{timestamp}.joblib"
        trainer.save_model(model, model_filename)
        
        logger.info("Model training completed successfully")
        logger.info(f"Trained model saved as: {model_filename}")
        
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        raise

if __name__ == "__main__":
    train_weather_model()
