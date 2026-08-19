import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.db.session import AsyncSessionLocal
from sqlalchemy import delete

@pytest.fixture(autouse=True)
async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == 'bulktest@example.com'))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == 'bulktest@example.com'))
        await session.commit()

@pytest.mark.asyncio
async def test_bulk_predictions_route_collision():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://testserver') as ac:
        await ac.post('/api/v1/signup', json={'email': 'bulktest@example.com', 'password': 'pass'})
        res = await ac.post('/api/v1/login/access-token', data={'username': 'bulktest@example.com', 'password': 'pass'})
        token = res.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        response = await ac.get('/api/v1/securities/predictions/bulk', headers=headers)
        assert response.status_code == 200, f'Route collision occurred: {response.status_code} - {response.text}'
