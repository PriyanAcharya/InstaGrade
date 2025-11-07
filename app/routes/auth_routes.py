# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app import db, models, schemas, auth
from sqlalchemy.future import select

router = APIRouter()

@router.post("/signup", response_model=schemas.UserOut)
async def signup(user: schemas.UserCreate, session: AsyncSession = Depends(db.get_session)):
    # Check if user already exists
    existing_user = await session.execute(select(models.User).where(models.User.email == user.email))
    if existing_user.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(name=user.name, email=user.email, password=hashed_pw, role=user.role)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(db.get_session)):
    result = await session.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar()

    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
async def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_use_
