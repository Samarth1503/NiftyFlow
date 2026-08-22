from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db
from backend.models.contact import ContactMessage

router = APIRouter()

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.post("")
async def create_contact(
    contact_in: ContactCreate,
    session: AsyncSession = Depends(get_db)
):
    contact = ContactMessage(**contact_in.model_dump())
    session.add(contact)
    await session.flush()
    return {"message": "Message sent successfully"}
