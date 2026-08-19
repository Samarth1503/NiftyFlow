import pytest
from backend.worker.ml_tasks import _generate_all_predictions
from backend.db.session import AsyncSessionLocal
from sqlalchemy.future import select
from sqlalchemy import delete
from backend.models.prediction import Prediction
from backend.models.security import Security
from backend.models.historical_price import HistoricalPrice
from datetime import datetime
import asyncio

@pytest.fixture(autouse=True)
async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Prediction))
        await session.execute(delete(HistoricalPrice))
        await session.execute(delete(Security).where(Security.symbol == 'RELIANCE'))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Prediction))
        await session.execute(delete(HistoricalPrice))
        await session.execute(delete(Security).where(Security.symbol == 'RELIANCE'))
        await session.commit()

@pytest.mark.asyncio
async def test_ml_pipeline_generates_predictions():
    # 1. Ensure we have at least one valid security
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Security).where(Security.symbol == 'RELIANCE'))
        sec = result.scalars().first()
        if not sec:
            sec = Security(symbol='RELIANCE', name='Reliance', exchange='NSE')
            session.add(sec)
            await session.commit()
            await session.refresh(sec)
            
    # 2. Run the Celery task logic directly in the same event loop
    from backend.worker.ml_tasks import _generate_all_predictions
    import backend.worker.ml_tasks
    
    # Mock _get_all_securities to ONLY return our test security
    # so we don't fetch history for 2500+ securities!
    from unittest.mock import patch
    
    with patch('backend.worker.ml_tasks._get_all_securities', return_value=[sec]):
        import pandas as pd
        from datetime import datetime, timedelta
        
        # We need at least 60 rows for XGBoost features to generate
        dates = [datetime.now() - timedelta(days=x) for x in range(100)]
        dummy_df = pd.DataFrame({'Close': [100.0] * 100}, index=dates)

        with patch('backend.worker.ml_tasks.market_data_provider.get_history', return_value=dummy_df):
            result = await _generate_all_predictions()
        
    assert result is True, "Task should complete successfully"

    # 3. Verify that predictions were written to the database
    async with AsyncSessionLocal() as session:
        pred_res = await session.execute(select(Prediction).where(Prediction.security_id == sec.id))
        prediction = pred_res.scalars().first()
        
        assert prediction is not None, "Prediction should be created"
        assert prediction.predicted_score > 0, "Score should be populated"
        assert prediction.model_version == "v2.0-xgb", "Model version should be v2.0-xgb"
        assert isinstance(prediction.prediction_date, datetime), "Prediction date should be set"
