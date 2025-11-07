# app/tasks.py
import os
import json
import logging
from celery import Celery
from typing import List

from .executor.docker_runner import run_code_in_docker
from .utils import compare_outputs, detect_plagiarism_for_assignment

# --- Celery config (reads env, fallback defaults) ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND = os.getenv("CELERY_BACKEND", "redis://redis:6379/1")

celery = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_BACKEND)
celery.conf.task_annotations = {"*": {"rate_limit": "10/s"}}

logger = logging.getLogger(__name__)


# NOTE: Integrate with your app.crud functions
# Expected crud functions in your repo:
# - crud.get_submission(submission_id) -> returns object with file_path, language, assignment_id, student_id
# - crud.get_testcases_for_assignment(assignment_id) -> returns list of testcases with input_path, expected_output_path, points
# - crud.save_evaluation_result(submission_id, result_dict) -> store result and status

# We'll import crud relatively; backend team should implement these functions.
try:
    from . import crud  # your backend's DB helper module
except Exception:
    crud = None
    logger.warning("Could not import crud module. You must wire DB integration.")


@celery.task(bind=True)
def evaluate_submission_task(self, submission_id: int):
    """
    Celery task that grades a submission end-to-end.
    """
    if crud is None:
        # For demo/dev: submission_id can be treated as a file path string
        # Return a helpful error for integration
        return {"status": "error", "message": "crud module not available; integrate with backend CRUD."}

    submission = crud.get_submission(submission_id)
    if not submission:
        return {"status": "error", "message": "submission not found"}

    assignment_id = submission.assignment_id
    testcases = crud.get_testcases_for_assignment(assignment_id)
    results = []
    total_points = 0
    earned_points = 0
    total_time = 0.0

    for tc in testcases:
        input_path = tc.input_path
        expected_out_path = tc.expected_output_path
        points = tc.points or 0
        total_points += points

        # run inside docker
        run_res = run_code_in_docker(submission.language, submission.file_path, input_path, timeout=tc.timeout or 3)

        if run_res.get("status") == "timeout":
            passed = False
            stdout = ""
            stderr = "timeout"
        elif run_res.get("status") == "runtime_error":
            passed = False
            stdout = run_res.get("stdout", "")
            stderr = run_res.get("stderr", run_res.get("message", "runtime error"))
        elif run_res.get("status") == "success":
            stdout = run_res.get("stdout", "")
            stderr = run_res.get("stderr", "")
            # read expected output
            if os.path.exists(expected_out_path):
                expected = open(expected_out_path).read()
            else:
                expected = ""
            passed = compare_outputs(stdout, expected)
        else:
            passed = False
            stdout = run_res.get("stdout", "")
            stderr = run_res.get("stderr", run_res.get("message", "error"))

        if passed:
            earned_points += points

        exec_time = run_res.get("execution_time", 0.0)
        total_time += float(exec_time or 0.0)

        results.append({
            "test_case_id": tc.id,
            "passed": passed,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": exec_time,
            "points_awarded": points if passed else 0,
        })

    avg_time = total_time / max(1, len(testcases))

    eval_summary = {
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "student_id": submission.student_id,
        "total_points": total_points,
        "earned_points": earned_points,
        "avg_execution_time": round(avg_time, 3),
        "details": results,
    }

    # Save result in DB
    try:
        crud.save_evaluation_result(submission_id, eval_summary)
    except Exception as e:
        logger.exception("Failed to save evaluation result: %s", e)

    # Optional: run plagiarism detection for the whole assignment and save flags
    try:
        plagiarism_flags = detect_plagiarism_for_assignment(assignment_id)
        if plagiarism_flags:
            crud.save_plagiarism_flags(assignment_id, plagiarism_flags)
            eval_summary["plagiarism_flags"] = plagiarism_flags
    except Exception:
        logger.exception("Plagiarism check failed")

    return eval_summary
