# app/routes/analytics_routes.py
from fastapi import APIRouter, Depends, HTTPException
from app import utils, crud, auth
from typing import List

router = APIRouter()

@router.get("/plagiarism/{assignment_id}")
async def check_plagiarism(assignment_id: int,
                           current_user=Depends(auth.get_current_user)):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can run plagiarism checks")

    try:
        results = utils.detect_plagiarism_for_assignment(assignment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"assignment_id": assignment_id, "flagged_pairs": results}
