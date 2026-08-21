from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError

from backend.core.config import settings
from backend.db.session import get_db
from backend.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")
SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=403, detail="Could not validate credentials")
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(status_code=403, detail="Could not validate credentials")
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Enable Row-Level Security for this transaction
    from sqlalchemy import text
    if session.bind and session.bind.dialect.name == 'postgresql':
        await session.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": str(user.id)})
    # DO NOT commit here. We need the current transaction to remain open so that the is_local=true 
    # setting applies to the queries/inserts in the route handler.
    
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user

CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]
