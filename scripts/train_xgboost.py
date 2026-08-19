import asyncio
import os
import sys
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from datetime import datetime, timezone

# Adjust path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.session import AsyncSessionLocal
from backend.models.security import Security
from backend.models.prediction import Prediction
from backend.utils.market import format_yf_symbol
from sqlalchemy.future import select

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators as features."""
    if len(df) < 200:
        return pd.DataFrame() # Not enough data
        
    # Moving Averages
    df['ma_10'] = df['Close'].rolling(window=10).mean()
    df['ma_50'] = df['Close'].rolling(window=50).mean()
    df['ma_200'] = df['Close'].rolling(window=200).mean()
    
    # Returns
    df['return_1d'] = df['Close'].pct_change(1)
    df['return_5d'] = df['Close'].pct_change(5)
    
    # Volatility
    df['volatility_20d'] = df['return_1d'].rolling(window=20).std()
    
    # Target: Will the price be higher 5 days from now? (Shift backwards)
    df['target_forward_5d'] = df['Close'].shift(-5)
    df['target'] = (df['target_forward_5d'] > df['Close']).astype(int)
    
    # Drop NaNs that were created by rolling windows and shifting
    # We keep the last row for prediction, so we must fill or handle its target
    
    return df

async def train_and_predict_for_security(session, security):
    yf_symbol = format_yf_symbol(security.symbol, security.exchange)
    logger.info(f"Fetching historical data for {yf_symbol}")
    
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period="2y")
    
    if df.empty or len(df) < 200:
        logger.warning(f"Not enough historical data for {yf_symbol}. Skipping.")
        return
        
    df = engineer_features(df)
    if df.empty:
        return
        
    # Prepare training data (excluding the last 5 days where target is NaN)
    train_df = df.dropna(subset=['ma_200', 'target_forward_5d']).copy()
    
    features = ['ma_10', 'ma_50', 'ma_200', 'return_1d', 'return_5d', 'volatility_20d']
    X = train_df[features]
    y = train_df['target']
    
    if len(X) < 50:
        logger.warning(f"Insufficient training rows for {yf_symbol} after dropping NaNs.")
        return
        
    # --- MODEL EVALUATION (Time-Series Split) ---
    # We use the first 80% of time for training, and the last 20% to test accuracy
    split_idx = int(len(X) * 0.8)
    X_train_eval, X_test_eval = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train_eval, y_test_eval = y.iloc[:split_idx], y.iloc[split_idx:]
    
    eval_model = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    eval_model.fit(X_train_eval, y_train_eval)
    y_pred_eval = eval_model.predict(X_test_eval)
    
    from sklearn.metrics import accuracy_score, precision_score
    acc = accuracy_score(y_test_eval, y_pred_eval)
    # Zero_division=0 handles edge cases where the model never predicts a 1
    prec = precision_score(y_test_eval, y_pred_eval, zero_division=0)
    
    logger.info(f"[{yf_symbol}] Evaluation Metrics - Accuracy: {acc:.2%}, Precision: {prec:.2%}")

    # --- FINAL PRODUCTION TRAINING ---
    # Now train on the ENTIRE dataset so the final prediction uses the most recent data
    logger.info(f"Training final XGBoost model for {yf_symbol} with {len(X)} samples...")
    model = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    
    # Predict for the most recent day
    latest_data = df.iloc[-1:]
    X_latest = latest_data[features]
    
    # Handle possible NaNs in the latest row due to missing values
    if X_latest.isnull().values.any():
        logger.warning(f"NaN features in latest row for {yf_symbol}. Filling with mean/forward fill.")
        X_latest = X_latest.ffill().fillna(0)
        
    prob_up = model.predict_proba(X_latest)[0][1] # Probability of class 1 (price goes up)
    
    logger.info(f"[{yf_symbol}] 5-Day Outperformance Probability: {prob_up:.2%}")
    
    # Save to DB
    # Delete old prediction for this security if we only keep the latest
    await session.execute(
        Prediction.__table__.delete().where(Prediction.security_id == security.id)
    )
    
    prediction = Prediction(
        security_id=security.id,
        predicted_score=float(prob_up),
        model_version="xgb-v1.0"
    )
    session.add(prediction)
    await session.commit()
    logger.info(f"Saved prediction for {yf_symbol} to DB.")

async def main():
    logger.info("Starting ML Training Pipeline...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Security))
        securities = result.scalars().all()
        
        if not securities:
            logger.info("No securities found in database. Exiting.")
            return
            
        for sec in securities:
            try:
                await train_and_predict_for_security(session, sec)
            except Exception as e:
                logger.error(f"Failed to process {sec.symbol}: {str(e)}")
                
    logger.info("ML Training Pipeline Completed.")

if __name__ == "__main__":
    asyncio.run(main())
