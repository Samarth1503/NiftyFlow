from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select
from jose import jwt, JWTError

from backend.api.deps import SessionDep, CurrentUser
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.core.config import settings
from backend.models.user import User
from backend.models.schemas import Token, UserCreate, UserResponse, PasswordRecovery, PasswordReset
from backend.utils.email import send_password_reset_email
from backend.api.limiter import limiter

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login_access_token(request: Request, session: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer"
    }

@router.post("/signup", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def signup(request: Request, session: SessionDep, user_in: UserCreate):
    result = await session.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(new_user)
    await session.flush()
    await session.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user

@router.post('/password-recovery')
async def recover_password(body: PasswordRecovery, session: SessionDep, background_tasks: BackgroundTasks):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalars().first()
    if not user:
        return {'message': 'If an account exists, a password reset link has been generated.'}
    
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {'exp': expire, 'sub': str(user.id), 'type': 'reset'}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    background_tasks.add_task(send_password_reset_email, user.email, encoded_jwt)
    
    return {'message': 'If an account exists, a password reset link has been generated.', 'token': encoded_jwt}

@router.post('/reset-password')
async def reset_password(body: PasswordReset, session: SessionDep):
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get('sub')
        token_type: str = payload.get('type')
        if user_id is None or token_type != 'reset':
            raise HTTPException(status_code=400, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=400, detail='Invalid or expired token')
        
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
        
    user.hashed_password = get_password_hash(body.new_password)
    session.add(user)
    await session.flush()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(user.id, expires_delta=access_token_expires)
    
    return {
        "message": "Password updated successfully",
        "access_token": new_access_token,
        "token_type": "bearer"
    }

