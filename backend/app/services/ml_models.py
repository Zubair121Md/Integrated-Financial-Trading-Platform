"""
Machine Learning models service for algorithmic trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import boto3
from sqlalchemy.orm import Session

from app.models.market_data import MarketData
from app.models.asset import Asset
from app.config import settings


class MLModelService:
    """Service for training and managing ML models for trading."""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.models = {}
        self.s3_client = boto3.client('s3') if settings.aws_access_key_id else None
    
    async def train_lstm_model(
        self,
        asset_id: int,
        lookback_days: int = 60,
        prediction_days: int = 1,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train LSTM model for price prediction."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Prepare features and targets
        X, y = self._prepare_lstm_data(data, lookback_days, prediction_days)
        
        if len(X) < 100:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Scale data
        X_train_scaled = self.scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1]))
        X_test_scaled = self.scaler.transform(X_test.reshape(-1, X_test.shape[-1]))
        
        X_train_scaled = X_train_scaled.reshape(X_train.shape)
        X_test_scaled = X_test_scaled.reshape(X_test.shape)
        
        # Build LSTM model
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(lookback_days, X.shape[2])),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        
        # Train model
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        history = model.fit(
            X_train_scaled, y_train,
            epochs=100,
            batch_size=32,
            validation_data=(X_test_scaled, y_test),
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Evaluate model
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model
        model_path = f"models/lstm_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        model.save(model_path)
        
        # Upload to S3 if available
        if self.s3_client and settings.s3_bucket_name:
            s3_key = f"ml-models/{model_path}"
            self.s3_client.upload_file(model_path, settings.s3_bucket_name, s3_key)
            model_path = f"s3://{settings.s3_bucket_name}/{s3_key}"
        
        return {
            "status": "success",
            "model_type": "LSTM",
            "asset_id": asset_id,
            "model_path": model_path,
            "metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2)
            },
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    async def train_random_forest_model(
        self,
        asset_id: int,
        lookback_days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train Random Forest model for price prediction."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Prepare features and targets
        X, y = self._prepare_tabular_data(data, lookback_days)
        
        if len(X) < 100:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Get feature importance
        feature_importance = dict(zip(
            [f"feature_{i}" for i in range(X.shape[1])],
            model.feature_importances_
        ))
        
        # Save model
        model_path = f"models/rf_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        joblib.dump(model, model_path)
        
        return {
            "status": "success",
            "model_type": "RandomForest",
            "asset_id": asset_id,
            "model_path": model_path,
            "metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2)
            },
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    async def train_svm_model(
        self,
        asset_id: int,
        lookback_days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train SVM model for price prediction."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Prepare features and targets
        X, y = self._prepare_tabular_data(data, lookback_days)
        
        if len(X) < 100:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Train model
        model = SVR(kernel='rbf', C=1.0, gamma='scale')
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model and scaler
        model_path = f"models/svm_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        scaler_path = f"models/svm_scaler_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        return {
            "status": "success",
            "model_type": "SVM",
            "asset_id": asset_id,
            "model_path": model_path,
            "scaler_path": scaler_path,
            "metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2)
            },
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    async def predict_price(
        self,
        model_path: str,
        model_type: str,
        recent_data: pd.DataFrame,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Make price prediction using trained model."""
        
        try:
            if model_type == "LSTM":
                return await self._predict_lstm(model_path, recent_data, lookback_days)
            elif model_type == "RandomForest":
                return await self._predict_random_forest(model_path, recent_data, lookback_days)
            elif model_type == "SVM":
                return await self._predict_svm(model_path, recent_data, lookback_days)
            else:
                return {"status": "error", "message": f"Unsupported model type: {model_type}"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_historical_data(self, asset_id: int, days: int, db: Session) -> pd.DataFrame:
        """Get historical market data for an asset."""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        market_data = db.query(MarketData).filter(
            MarketData.asset_id == asset_id,
            MarketData.timestamp >= cutoff_date
        ).order_by(MarketData.timestamp).all()
        
        if not market_data:
            return pd.DataFrame()
        
        data = []
        for md in market_data:
            data.append({
                'timestamp': md.timestamp,
                'price': md.price,
                'open': md.open_price or md.price,
                'high': md.high_price or md.price,
                'low': md.low_price or md.price,
                'volume': md.volume or 0,
                'rsi': md.rsi or 0,
                'macd': md.macd or 0,
                'sma_20': md.sma_20 or 0,
                'sma_50': md.sma_50 or 0
            })
        
        return pd.DataFrame(data)
    
    def _prepare_lstm_data(
        self, 
        data: pd.DataFrame, 
        lookback_days: int, 
        prediction_days: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM training."""
        
        # Select features
        features = ['price', 'open', 'high', 'low', 'volume', 'rsi', 'macd', 'sma_20', 'sma_50']
        feature_data = data[features].values
        
        # Create sequences
        X, y = [], []
        for i in range(lookback_days, len(feature_data) - prediction_days + 1):
            X.append(feature_data[i-lookback_days:i])
            y.append(feature_data[i+prediction_days-1, 0])  # Predict price
        
        return np.array(X), np.array(y)
    
    def _prepare_tabular_data(
        self, 
        data: pd.DataFrame, 
        lookback_days: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for tabular model training."""
        
        # Create lagged features
        features = ['price', 'open', 'high', 'low', 'volume', 'rsi', 'macd', 'sma_20', 'sma_50']
        
        X_data = []
        for i in range(lookback_days, len(data)):
            row = []
            for j in range(lookback_days):
                for feature in features:
                    row.append(data[feature].iloc[i-j-1])
            X_data.append(row)
        
        y_data = data['price'].iloc[lookback_days:].values
        
        return np.array(X_data), y_data
    
    async def _predict_lstm(
        self, 
        model_path: str, 
        recent_data: pd.DataFrame, 
        lookback_days: int
    ) -> Dict[str, Any]:
        """Make prediction using LSTM model."""
        
        # Load model
        model = tf.keras.models.load_model(model_path)
        
        # Prepare data
        features = ['price', 'open', 'high', 'low', 'volume', 'rsi', 'macd', 'sma_20', 'sma_50']
        feature_data = recent_data[features].tail(lookback_days).values
        
        # Scale data
        feature_data_scaled = self.scaler.transform(feature_data.reshape(-1, feature_data.shape[-1]))
        feature_data_scaled = feature_data_scaled.reshape(1, lookback_days, -1)
        
        # Make prediction
        prediction = model.predict(feature_data_scaled)[0][0]
        
        return {
            "status": "success",
            "prediction": float(prediction),
            "confidence": 0.8,  # Placeholder
            "model_type": "LSTM"
        }
    
    async def _predict_random_forest(
        self, 
        model_path: str, 
        recent_data: pd.DataFrame, 
        lookback_days: int
    ) -> Dict[str, Any]:
        """Make prediction using Random Forest model."""
        
        # Load model
        model = joblib.load(model_path)
        
        # Prepare data
        X, _ = self._prepare_tabular_data(recent_data, lookback_days)
        if len(X) == 0:
            return {"status": "error", "message": "Insufficient data for prediction"}
        
        # Make prediction
        prediction = model.predict(X[-1:])[0]
        
        return {
            "status": "success",
            "prediction": float(prediction),
            "confidence": 0.7,  # Placeholder
            "model_type": "RandomForest"
        }
    
    async def _predict_svm(
        self, 
        model_path: str, 
        recent_data: pd.DataFrame, 
        lookback_days: int
    ) -> Dict[str, Any]:
        """Make prediction using SVM model."""
        
        # Load model and scaler
        model = joblib.load(model_path)
        scaler_path = model_path.replace('.joblib', '_scaler.joblib')
        scaler = joblib.load(scaler_path)
        
        # Prepare data
        X, _ = self._prepare_tabular_data(recent_data, lookback_days)
        if len(X) == 0:
            return {"status": "error", "message": "Insufficient data for prediction"}
        
        # Scale and predict
        X_scaled = scaler.transform(X[-1:])
        prediction = model.predict(X_scaled)[0]
        
        return {
            "status": "success",
            "prediction": float(prediction),
            "confidence": 0.6,  # Placeholder
            "model_type": "SVM"
        }
