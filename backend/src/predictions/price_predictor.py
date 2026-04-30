"""
AI Price Predictor using machine learning models trained on historical forex data.
Combines multiple ML techniques for robust price movement predictions.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import pickle
import os
from datetime import datetime
from src.utils.logger import logger


class PricePredictor:
    """ML-based price movement predictor for forex pairs"""
    
    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(__file__), '../../models'
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.rf_model = None
        self.lr_model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
    
    def prepare_features(self, df: pd.DataFrame, lookback: int = 14) -> tuple:
        """
        Prepare ML features from OHLC data.
        
        Args:
            df: DataFrame with OHLC data
            lookback: Number of periods to look back for features
        
        Returns:
            Tuple of (X, y) where X is features array, y is labels
        """
        try:
            if len(df) < lookback + 1:
                logger.warning(f"Not enough data for lookback={lookback}")
                return np.array([]), np.array([])
            
            # Normalize column names to lowercase
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            # Ensure required columns exist (volume is optional for forex)
            required_cols = ['open', 'high', 'low', 'close']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return np.array([]), np.array([])
            
            # Calculate technical indicators as features
            # Price changes and returns
            df['returns'] = df['close'].pct_change()
            df['high_low_ratio'] = (df['high'] - df['low']) / df['low']
            df['close_open_ratio'] = (df['close'] - df['open']) / df['open']
            
            # SMA features
            for period in [7, 14, 21]:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                df[f'price_sma_{period}'] = (df['close'] - df[f'sma_{period}']) / df[f'sma_{period}']
            
            # RSI features
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Volatility features
            df['volatility'] = df['returns'].rolling(window=14).std()
            df['atr'] = self._calculate_atr(df)
            
            # Volume features
            if 'volume' in df.columns:
                df['volume_sma'] = df['volume'].rolling(window=14).mean()
                df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 1e-8)
            
            # Target: 1 if next close > current close, 0 otherwise
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
            
            # Remove NaN values
            df = df.dropna()
            
            # Select feature columns
            feature_cols = [
                'returns', 'high_low_ratio', 'close_open_ratio',
                'sma_7', 'sma_14', 'sma_21',
                'price_sma_7', 'price_sma_14', 'price_sma_21',
                'rsi', 'volatility', 'atr'
            ]
            
            # Add volume ratio if available
            if 'volume_ratio' in df.columns:
                feature_cols.append('volume_ratio')
            
            feature_cols = [col for col in feature_cols if col in df.columns]
            
            X = df[feature_cols].values
            y = df['target'].values
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            logger.info(f"Prepared {len(X)} samples with {len(feature_cols)} features")
            return X_scaled, y
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.array([]), np.array([])
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def train(self, df: pd.DataFrame, symbol: str = "EURUSD") -> bool:
        """
        Train ML models on historical data.
        
        Args:
            df: DataFrame with OHLC data
            symbol: Currency pair for model identification
        
        Returns:
            True if training successful, False otherwise
        """
        try:
            logger.info(f"Training price predictor for {symbol}")
            
            X, y = self.prepare_features(df)
            
            if len(X) == 0:
                logger.warning("No data available for training")
                return False
            
            # Check if we have both classes
            if len(np.unique(y)) < 2:
                logger.warning("Insufficient class diversity in target variable")
                return False
            
            # Train Random Forest
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                n_jobs=-1
            )
            self.rf_model.fit(X, y)
            
            # Train Logistic Regression
            self.lr_model = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
            self.lr_model.fit(X, y)
            
            self.is_trained = True
            
            # Save models
            self._save_models(symbol)
            
            rf_score = self.rf_model.score(X, y)
            lr_score = self.lr_model.score(X, y)
            logger.info(f"Training complete. RF accuracy: {rf_score:.3f}, LR accuracy: {lr_score:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training price predictor: {e}")
            return False
    
    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predict next price movement.
        
        Args:
            df: DataFrame with OHLC data (recent data point last)
        
        Returns:
            Dict with prediction results:
            {
                'direction': 'UP' or 'DOWN',
                'confidence': 0.0-1.0,
                'rf_probability': probability from random forest,
                'lr_probability': probability from logistic regression,
                'ensemble_probability': averaged probability
            }
        """
        try:
            if not self.is_trained or self.rf_model is None:
                logger.warning("Model not trained yet")
                return self._no_prediction()
            
            X, _ = self.prepare_features(df)
            
            if len(X) == 0:
                logger.warning("Could not prepare features for prediction")
                return self._no_prediction()
            
            # Use most recent sample
            x_latest = X[-1:, :]
            
            # Get probabilities from both models
            rf_proba = self.rf_model.predict_proba(x_latest)[0]
            lr_proba = self.lr_model.predict_proba(x_latest)[0]
            
            # Ensemble prediction (weighted average)
            # rf_proba[1] = probability of UP (class 1)
            # lr_proba[1] = probability of UP (class 1)
            ensemble_proba = (rf_proba[1] + lr_proba[1]) / 2.0
            
            # Determine direction and confidence
            direction = "UP" if ensemble_proba > 0.5 else "DOWN"
            confidence = max(ensemble_proba, 1 - ensemble_proba)
            
            prediction = {
                'direction': direction,
                'confidence': float(confidence),
                'rf_probability': float(rf_proba[1]),  # Probability of UP from RF
                'lr_probability': float(lr_proba[1]),  # Probability of UP from LR
                'ensemble_probability': float(ensemble_proba),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Prediction - Direction: {direction}, Confidence: {confidence:.3f}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return self._no_prediction()
    
    def _no_prediction(self) -> dict:
        """Return neutral prediction"""
        return {
            'direction': 'NEUTRAL',
            'confidence': 0.0,
            'rf_probability': 0.5,
            'lr_probability': 0.5,
            'ensemble_probability': 0.5,
            'timestamp': datetime.now().isoformat()
        }
    
    def _save_models(self, symbol: str):
        """Save trained models to disk"""
        try:
            rf_path = os.path.join(self.model_dir, f"rf_model_{symbol}.pkl")
            lr_path = os.path.join(self.model_dir, f"lr_model_{symbol}.pkl")
            scaler_path = os.path.join(self.model_dir, f"scaler_{symbol}.pkl")
            
            with open(rf_path, 'wb') as f:
                pickle.dump(self.rf_model, f)
            with open(lr_path, 'wb') as f:
                pickle.dump(self.lr_model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info(f"Models saved for {symbol}")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self, symbol: str) -> bool:
        """Load pre-trained models from disk"""
        try:
            rf_path = os.path.join(self.model_dir, f"rf_model_{symbol}.pkl")
            lr_path = os.path.join(self.model_dir, f"lr_model_{symbol}.pkl")
            scaler_path = os.path.join(self.model_dir, f"scaler_{symbol}.pkl")
            
            if not all(os.path.exists(p) for p in [rf_path, lr_path, scaler_path]):
                logger.warning(f"Model files not found for {symbol}")
                return False
            
            with open(rf_path, 'rb') as f:
                self.rf_model = pickle.load(f)
            with open(lr_path, 'rb') as f:
                self.lr_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Models loaded for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False


# Singleton instance
price_predictor = PricePredictor()
