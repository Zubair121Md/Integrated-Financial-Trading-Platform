"""
Advanced ML models service with XGBoost and VGG integration.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
import cv2
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.applications import VGG16, VGG19
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import boto3
from sqlalchemy.orm import Session

from app.models.market_data import MarketData
from app.models.asset import Asset
from app.config import settings


class AdvancedMLService:
    """Service for advanced ML models including XGBoost and VGG."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.models = {}
        self.s3_client = boto3.client('s3') if settings.aws_access_key_id else None
    
    async def train_xgboost_model(
        self,
        asset_id: int,
        lookback_days: int = 60,
        prediction_horizon: int = 1,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train XGBoost model for price prediction."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Prepare features and targets
        X, y = self._prepare_xgboost_data(data, lookback_days, prediction_horizon)
        
        if len(X) < 100:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        model = xgb.XGBRegressor(
            n_estimators=1000,
            max_depth=6,
            learning_rate=0.01,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            early_stopping_rounds=50,
            eval_metric='rmse'
        )
        
        # Train with validation set
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Evaluate model
        y_pred = model.predict(X_test_scaled)
        mse = np.mean((y_test - y_pred) ** 2)
        mae = np.mean(np.abs(y_test - y_pred))
        r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_squared_error')
        cv_rmse = np.sqrt(-cv_scores.mean())
        
        # Get feature importance
        feature_importance = dict(zip(
            [f"feature_{i}" for i in range(X.shape[1])],
            model.feature_importances_
        ))
        
        # Save model
        model_path = f"models/xgboost_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        scaler_path = f"models/xgboost_scaler_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        return {
            "status": "success",
            "model_type": "XGBoost",
            "asset_id": asset_id,
            "model_path": model_path,
            "scaler_path": scaler_path,
            "metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2),
                "cv_rmse": float(cv_rmse)
            },
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    async def train_vgg_model(
        self,
        asset_id: int,
        lookback_days: int = 60,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train VGG model for pattern recognition in price charts."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Generate chart images and labels
        X_images, y_labels = self._prepare_vgg_data(data, lookback_days)
        
        if len(X_images) < 50:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_images, y_labels, test_size=0.2, random_state=42, stratify=y_labels
        )
        
        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        # Build VGG model
        base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        
        # Freeze base model layers
        for layer in base_model.layers:
            layer.trainable = False
        
        # Add custom layers
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        predictions = Dense(len(np.unique(y_train_encoded)), activation='softmax')(x)
        
        model = Model(inputs=base_model.input, outputs=predictions)
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Train model
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        history = model.fit(
            X_train, y_train_encoded,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test_encoded),
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Evaluate model
        test_loss, test_accuracy = model.evaluate(X_test, y_test_encoded, verbose=0)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_classes = np.argmax(y_pred, axis=1)
        
        # Classification report
        class_report = classification_report(
            y_test_encoded, y_pred_classes,
            target_names=self.label_encoder.classes_,
            output_dict=True
        )
        
        # Save model
        model_path = f"models/vgg_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        model.save(model_path)
        
        return {
            "status": "success",
            "model_type": "VGG16",
            "asset_id": asset_id,
            "model_path": model_path,
            "metrics": {
                "test_accuracy": float(test_accuracy),
                "test_loss": float(test_loss),
                "classification_report": class_report
            },
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    async def train_ensemble_model(
        self,
        asset_id: int,
        lookback_days: int = 60,
        db: Session = None
    ) -> Dict[str, Any]:
        """Train ensemble model combining multiple ML techniques."""
        
        # Get historical data
        data = self._get_historical_data(asset_id, lookback_days * 2, db)
        if data.empty:
            return {"status": "error", "message": "Insufficient historical data"}
        
        # Prepare data for different models
        X_tabular, y_tabular = self._prepare_xgboost_data(data, lookback_days, 1)
        X_lstm, y_lstm = self._prepare_lstm_data(data, lookback_days, 1)
        
        if len(X_tabular) < 100 or len(X_lstm) < 100:
            return {"status": "error", "message": "Insufficient data for training"}
        
        # Train individual models
        xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
        xgb_model.fit(X_tabular, y_tabular)
        
        # LSTM model (simplified)
        lstm_model = self._build_simple_lstm(X_lstm.shape[1], X_lstm.shape[2])
        lstm_model.fit(X_lstm, y_lstm, epochs=10, verbose=0)
        
        # Create ensemble predictions
        xgb_pred = xgb_model.predict(X_tabular)
        lstm_pred = lstm_model.predict(X_lstm).flatten()
        
        # Combine predictions (simple average)
        ensemble_pred = (xgb_pred + lstm_pred) / 2
        
        # Evaluate ensemble
        mse = np.mean((y_tabular - ensemble_pred) ** 2)
        mae = np.mean(np.abs(y_tabular - ensemble_pred))
        r2 = 1 - (np.sum((y_tabular - ensemble_pred) ** 2) / np.sum((y_tabular - np.mean(y_tabular)) ** 2))
        
        # Save models
        xgb_path = f"models/ensemble_xgb_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        lstm_path = f"models/ensemble_lstm_asset_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        
        joblib.dump(xgb_model, xgb_path)
        lstm_model.save(lstm_path)
        
        return {
            "status": "success",
            "model_type": "Ensemble",
            "asset_id": asset_id,
            "xgb_path": xgb_path,
            "lstm_path": lstm_path,
            "metrics": {
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2)
            },
            "training_samples": len(X_tabular)
        }
    
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
    
    def _prepare_xgboost_data(
        self, 
        data: pd.DataFrame, 
        lookback_days: int, 
        prediction_horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for XGBoost training."""
        
        # Create technical indicators
        data['sma_5'] = data['price'].rolling(window=5).mean()
        data['sma_10'] = data['price'].rolling(window=10).mean()
        data['ema_12'] = data['price'].ewm(span=12).mean()
        data['ema_26'] = data['price'].ewm(span=26).mean()
        data['rsi'] = self._calculate_rsi(data['price'])
        data['macd'] = data['ema_12'] - data['ema_26']
        data['bb_upper'], data['bb_middle'], data['bb_lower'] = self._calculate_bollinger_bands(data['price'])
        data['volatility'] = data['price'].rolling(window=20).std()
        data['price_change'] = data['price'].pct_change()
        data['volume_change'] = data['volume'].pct_change()
        
        # Create lagged features
        features = ['price', 'open', 'high', 'low', 'volume', 'rsi', 'macd', 
                   'sma_5', 'sma_10', 'sma_20', 'sma_50', 'bb_upper', 'bb_lower', 
                   'volatility', 'price_change', 'volume_change']
        
        X_data = []
        for i in range(lookback_days, len(data) - prediction_horizon + 1):
            row = []
            for j in range(lookback_days):
                for feature in features:
                    if feature in data.columns:
                        row.append(data[feature].iloc[i-j-1])
                    else:
                        row.append(0)
            X_data.append(row)
        
        y_data = data['price'].iloc[lookback_days + prediction_horizon - 1:].values
        
        return np.array(X_data), y_data
    
    def _prepare_lstm_data(
        self, 
        data: pd.DataFrame, 
        lookback_days: int, 
        prediction_horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM training."""
        
        features = ['price', 'open', 'high', 'low', 'volume', 'rsi', 'macd', 'sma_20', 'sma_50']
        feature_data = data[features].values
        
        X, y = [], []
        for i in range(lookback_days, len(feature_data) - prediction_horizon + 1):
            X.append(feature_data[i-lookback_days:i])
            y.append(feature_data[i+prediction_horizon-1, 0])  # Predict price
        
        return np.array(X), np.array(y)
    
    def _prepare_vgg_data(
        self, 
        data: pd.DataFrame, 
        lookback_days: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare chart images and labels for VGG training."""
        
        images = []
        labels = []
        
        for i in range(lookback_days, len(data) - 5):
            # Create price chart image
            chart_data = data.iloc[i-lookback_days:i]
            image = self._create_chart_image(chart_data)
            images.append(image)
            
            # Create label based on future price movement
            current_price = data['price'].iloc[i]
            future_price = data['price'].iloc[i+5]
            price_change = (future_price - current_price) / current_price
            
            if price_change > 0.02:  # 2% increase
                labels.append('bullish')
            elif price_change < -0.02:  # 2% decrease
                labels.append('bearish')
            else:
                labels.append('neutral')
        
        return np.array(images), np.array(labels)
    
    def _create_chart_image(self, data: pd.DataFrame) -> np.ndarray:
        """Create a candlestick chart image from price data."""
        
        # Create a blank image
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        
        # Simple candlestick chart
        for i, (_, row) in enumerate(data.iterrows()):
            x = int((i / len(data)) * 200) + 12
            y_high = int(200 - (row['high'] - data['low'].min()) / (data['high'].max() - data['low'].min()) * 180) + 12
            y_low = int(200 - (row['low'] - data['low'].min()) / (data['high'].max() - data['low'].min()) * 180) + 12
            y_open = int(200 - (row['open'] - data['low'].min()) / (data['high'].max() - data['low'].min()) * 180) + 12
            y_close = int(200 - (row['close'] - data['low'].min()) / (data['high'].max() - data['low'].min()) * 180) + 12
            
            # Draw candlestick
            color = (0, 255, 0) if row['close'] > row['open'] else (255, 0, 0)
            cv2.line(img, (x, y_high), (x, y_low), color, 1)
            cv2.rectangle(img, (x-2, min(y_open, y_close)), (x+2, max(y_open, y_close)), color, -1)
        
        return img
    
    def _build_simple_lstm(self, timesteps: int, features: int) -> tf.keras.Model:
        """Build a simple LSTM model."""
        
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(timesteps, features)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(50, return_sequences=False),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(25),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Fill NaN with neutral RSI
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band.fillna(prices), sma.fillna(prices), lower_band.fillna(prices)
