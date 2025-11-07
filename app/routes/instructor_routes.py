# app/routes/instructor_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import db, models, schemas, auth
from datetime import datetime

router = APIRouter()

@router.post("/assignments", response_model=schemas.AssignmentOut)
async def create_assignment(assignment: schemas.AssignmentCreate,
                            current_user: models.User = Depends(auth.get_current_user),
                            session: AsyncSession = Depends(db.get_session)):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create assignments")

    new_assignment = models.Assignment(
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        created_by=current_user.id
    )
    session.add(new_assignment)
    await session.commit()
    await session.refresh(new_assignment)
    return new_assignment


@router.get("/assignments/{assignment_id}/submissions", response_model=list[schemas.SubmissionOut])
async def get_submissions(assignment_id: int, 
                          current_user: models.User = Depends(auth.get_current_user),
                          session: AsyncSession = Depends(db.get_session)):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can view submissions")

    result = await session.execute(select(models.Submission).where(models.Submission.assignment_id == assignment_id))
    submissions = result.scalars().all()
    return submissions
