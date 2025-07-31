"""
XGBoost-based Weather Model Trainer for Philadelphia
"""

import logging
import pandas as pd
import numpy as np
import joblib
import os
from typing import Any, Dict, Tuple
from datetime import datetime
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

logger = logging.getLogger(__name__)


class WeatherModelTrainer:
    """XGBoost-based trainer for Philadelphia weather prediction models."""
    
    def __init__(self, model_params: Dict = None):
        """
        Initialize the trainer with XGBoost parameters.
        
        Args:
            model_params: Dictionary of XGBoost parameters
        """
        self.model_params = model_params or {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
    
    def train_model(self, features_df: pd.DataFrame, target_column: str) -> Tuple[Any, Dict]:
        """
        Train an XGBoost model for Philadelphia weather prediction.
        
        Args:
            features_df: DataFrame with features
            target_column: Name of the target column
            
        Returns:
            Tuple of (trained model, training metrics)
        """
        logger.info(f"Training XGBoost model for target: {target_column}")
        
        # Prepare features and target
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")
        
        # Remove rows with missing target values
        df = features_df.dropna(subset=[target_column])
        
        # Separate features and target
        feature_columns = [col for col in df.columns if col != target_column and col != 'date']
        X = df[feature_columns]
        y = df[target_column]
        
        # Handle missing values in features
        X = X.fillna(0)  # Simple imputation
        
        # Convert to numeric
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        y = pd.to_numeric(y, errors='coerce').fillna(0)
        
        # Ensure target is binary for classification
        y = (y > 0.5).astype(int)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train XGBoost model
        model = xgb.XGBClassifier(**self.model_params)
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
        
        metrics = {
            'accuracy': accuracy,
            'auc': auc,
            'logloss': logloss,
            'cv_mean_auc': cv_scores.mean(),
            'cv_std_auc': cv_scores.std(),
            'n_samples': len(X),
            'n_features': len(feature_columns)
        }
        
        logger.info(f"Model trained with {len(X)} samples and {len(feature_columns)} features")
        logger.info(f"Test Accuracy: {accuracy:.4f}, AUC: {auc:.4f}, Log Loss: {logloss:.4f}")
        logger.info(f"CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Save feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("Top 10 most important features:")
        for i, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        
        # Save model and metrics
        os.makedirs('models', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"models/philly_weather_xgb_{target_column}_{timestamp}.joblib"
        metrics_filename = f"models/philly_weather_metrics_{target_column}_{timestamp}.json"
        
        joblib.dump(model, model_filename)
        feature_importance.to_csv(f"models/philly_feature_importance_{target_column}_{timestamp}.csv", index=False)
        
        # Save metrics
        import json
        with open(metrics_filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Model saved to {model_filename}")
        logger.info(f"Metrics saved to {metrics_filename}")
        logger.info(f"Feature importance saved to models/philly_feature_importance_{target_column}_{timestamp}.csv")
        
        return model, metrics
    
    def save_model(self, model: Any, filepath: str) -> None:
        """
        Save a trained model to disk.
        
        Args:
            model: Trained model
            filepath: Path to save model
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(model, filepath)
        logger.info(f"Model saved to {filepath}")
