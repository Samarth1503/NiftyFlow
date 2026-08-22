import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from backend.models.user import User
from backend.db.session import AsyncSessionLocal
from sqlalchemy import delete

test_email = "testuser@example.com"
test_password = "TestPassword123!"

@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    # Clean up test user before and after test
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == test_email))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == test_email))
        await session.commit()

@pytest.mark.asyncio
async def test_auth_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        
        # 1. Signup
        response = await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        assert data["email"] == test_email
        assert "id" in data

        # 2. Duplicate Signup should fail
        response_dup = await ac.post("/api/v1/signup", json={"email": test_email, "password": test_password})
        assert response_dup.status_code == 400

        # 3. Invalid Login should fail
        response_invalid = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response_invalid.status_code == 400

        # 4. Valid Login
        response_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": test_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response_login.status_code == 200, f"Login failed: {response_login.text}"
        token_data = response_login.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        token = token_data["access_token"]

        # 5. Get Current User (Me)
        response_me = await ac.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert response_me.status_code == 200, f"Me failed: {response_me.text}"
        me_data = response_me.json()
        assert me_data["email"] == test_email
        assert "id" in me_data

        # 6. Password Recovery
        response_recovery = await ac.post("/api/v1/password-recovery", json={"email": test_email})
        assert response_recovery.status_code == 200, f"Recovery failed: {response_recovery.text}"
        recovery_data = response_recovery.json()
        assert "If an account exists" in recovery_data["message"]
        assert "token" in recovery_data
        reset_token = recovery_data["token"]
        
        # 7. Reset Password (with valid token)
        new_password = "NewStrongPassword456!"
        response_reset = await ac.post("/api/v1/reset-password", json={"token": reset_token, "new_password": new_password})
        assert response_reset.status_code == 200, f"Reset failed: {response_reset.text}"
        reset_data = response_reset.json()
        assert reset_data["message"] == "Password updated successfully"
        assert "access_token" in reset_data  # verify seamless login token is returned
        
        # 8. Verify Old Password Fails
        response_old_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": test_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response_old_login.status_code == 400

        # 9. Verify New Password Succeeds
        response_new_login = await ac.post(
            "/api/v1/login/access-token",
            data={"username": test_email, "password": new_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response_new_login.status_code == 200

@pytest.mark.asyncio
async def test_invalid_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        
        # Missing token
        res1 = await ac.get("/api/v1/me")
        assert res1.status_code == 401
        
        # Invalid / Malformed token
        res2 = await ac.get("/api/v1/me", headers={"Authorization": "Bearer invalid.token.string"})
        assert res2.status_code == 403
        
        # Expired token
        from jose import jwt
        from backend.core.config import settings
        import datetime
        
        # datetime.datetime.utcnow() is deprecated, use datetime.datetime.now(datetime.timezone.utc)
        expired_token = jwt.encode(
            {"sub": "1", "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        res3 = await ac.get("/api/v1/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res3.status_code == 403

