# app/routes/student_routes.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import db, models, schemas, auth
import os, aiofiles
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads/"

@router.post("/submit/{assignment_id}")
async def submit_assignment(assignment_id: int, 
                            file: UploadFile = File(...),
                            current_user: models.User = Depends(auth.get_current_user),
                            session: AsyncSession = Depends(db.get_session)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{assignment_id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    submission = models.Submission(
        student_id=current_user.id,
        assignment_id=assignment_id,
        file_path=file_path,
        language="python",
        submitted_at=datetime.utcnow()
    )

    session.add(submission)
    await session.commit()
    return {"message": "Submission uploaded successfully"}
