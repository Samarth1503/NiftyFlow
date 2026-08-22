import asyncio
import logging
import time
import pandas as pd
import numpy as np

from backend.worker.celery_app import celery_app
from backend.db.session import WorkerSessionLocal
from backend.models.security import Security
from backend.models.prediction import Prediction
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
from backend.utils.market import format_yf_symbol
from backend.utils.market_data import market_data_provider
import xgboost as xgb

logger = logging.getLogger(__name__)

async def _get_all_securities():
    async with WorkerSessionLocal() as session:
        result = await session.execute(select(Security))
        return result.scalars().all()

async def _save_prediction(security_id: int, score: float):
    async with WorkerSessionLocal() as session:
        stmt = insert(Prediction).values(
            security_id=security_id,
            predicted_score=score,
            model_version="v2.0-xgb",
            prediction_date=func.now()
        )
        await session.execute(stmt)
        await session.commit()

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Simple feature engineering for XGBoost."""
    df = df.copy()
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['RSI_14'] = compute_rsi(df['Close'], 14)
    df['Volatility_10'] = df['Close'].rolling(window=10).std()
    
    # Returns
    df['Return_1d'] = df['Close'].pct_change(1)
    df['Return_5d'] = df['Close'].pct_change(5)
    
    # Target (will we go up tomorrow?)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    
    return df.dropna()

def compute_rsi(series: pd.Series, window: int = 14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window - 1, adjust=False).mean()
    ema_down = down.ewm(com=window - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def train_and_predict(hist: pd.DataFrame) -> float:
    try:
        df = extract_features(hist)
        if len(df) < 50: # Need enough data
            return 0.5
            
        features = ['SMA_5', 'SMA_20', 'RSI_14', 'Volatility_10', 'Return_1d', 'Return_5d']
        
        # We train on everything except the last row
        train_df = df.iloc[:-1]
        test_df = df.iloc[[-1]] # Predict for "tomorrow" based on today
        
        X_train = train_df[features]
        y_train = train_df['Target']
        X_test = test_df[features]
        
        model = xgb.XGBClassifier(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Predict probability of class 1 (UP)
        proba = model.predict_proba(X_test)[0][1]
        return float(proba)
        
    except Exception as e:
        logger.warning(f"XGBoost training failed: {e}")
        return 0.5

async def _generate_all_predictions(task_id: str = "test-task-id"):
    logger.info(f"event=task_started task_name=generate_predictions task_id={task_id}")
    
    securities = await _get_all_securities()
    
    # To avoid hammering API, we'll only do it for the first 50 stocks in a run, 
    # or limit it in some way.
    # Actually since it's an ML worker, let's just do all of them, but with market_data_provider delay
    
    for sec in securities:
        yf_symbol = format_yf_symbol(sec.symbol, sec.exchange)
        try:
            hist = await market_data_provider.get_history(yf_symbol, period="1y")
            
            if len(hist) < 60:
                continue
                
            score = await asyncio.to_thread(train_and_predict, hist)
            
            await _save_prediction(sec.id, score)
            logger.info(f"Generated XGB prediction for {sec.symbol}: {score:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to generate prediction for {sec.symbol}: {str(e)}")
            continue
            
    logger.info(f"event=task_completed task_name=generate_predictions task_id={task_id}")
    return True

@celery_app.task(bind=True)
def generate_predictions(self):
    task_id = self.request.id or "generate_predictions-test"
    from backend.db.session import engine
    engine.sync_engine.dispose()
    return asyncio.run(_generate_all_predictions(task_id))
