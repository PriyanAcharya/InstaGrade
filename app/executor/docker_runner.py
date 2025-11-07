# app/executor/docker_runner.py
import os
import time
import shutil
import tempfile
import logging

# prefer docker SDK, but allow subprocess fallback if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except Exception:
    DOCKER_AVAILABLE = False

import subprocess
from typing import Dict

logger = logging.getLogger(__name__)


def _run_subprocess(cmd: list, cwd: str, timeout: int):
    """Simple subprocess runner fallback (for local dev)."""
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )
        end = time.time()
        return {
            "status": "success" if proc.returncode == 0 else "runtime_error",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "execution_time": round(end - start, 3),
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "stdout": "", "stderr": "", "execution_time": timeout}


def run_code_in_docker(language: str, submission_file_path: str, input_file_path: str = None, timeout: int = 3) -> Dict:
    """
    Run a student's code inside a docker container (recommended).
    - language: "python", "cpp", "js"
    - submission_file_path: full path to student's file on host
    - input_file_path: optional path to input txt file on host
    - timeout: seconds
    Returns a dict with status, stdout, stderr, execution_time.
    """

    # Basic validation
    if not os.path.exists(submission_file_path):
        return {"status": "error", "message": "submission file not found"}

    tmpdir = tempfile.mkdtemp(prefix="exec_")
    try:
        # Copy submission and input to tmpdir (isolation)
        code_name = os.path.basename(submission_file_path)
        dst_code = os.path.join(tmpdir, code_name)
        shutil.copyfile(submission_file_path, dst_code)

        input_name = None
        if input_file_path and os.path.exists(input_file_path):
            input_name = os.path.basename(input_file_path)
            dst_input = os.path.join(tmpdir, input_name)
            shutil.copyfile(input_file_path, dst_input)
        else:
            dst_input = None

        if DOCKER_AVAILABLE:
            client = docker.from_env()
            # Choose image & command based on language
            if language == "python":
                image = "python:3.10-slim"
                cmd = f"bash -lc 'timeout {timeout}s python {code_name}'"
                if dst_input:
                    cmd = f"bash -lc 'timeout {timeout}s python {code_name} < {input_name}'"
            elif language == "cpp":
                # compile then run
                image = "gcc:12"
                # compile to a.out then run
                cmd = f"bash -lc 'g++ {code_name} -O2 -std=c++17 -o a.out && timeout {timeout}s ./a.out'"
                if dst_input:
                    cmd = f"bash -lc 'g++ {code_name} -O2 -std=c++17 -o a.out && timeout {timeout}s ./a.out < {input_name}'"
            elif language == "js":
                image = "node:18-alpine"
                cmd = f"bash -lc 'timeout {timeout}s node {code_name}'"
                if dst_input:
                    cmd = f"bash -lc 'timeout {timeout}s node {code_name} < {input_name}'"
            else:
                return {"status": "error", "message": f"unsupported language: {language}"}

            start = time.time()
            # run container with the tmpdir mounted
            try:
                container = client.containers.run(
                    image=image,
                    command=cmd,
                    volumes={tmpdir: {"bind": "/work", "mode": "ro"}},
                    working_dir="/work",
                    detach=True,
                    network_disabled=True,  # disable network for safety
                    mem_limit="256m",
                )
                wait_result = container.wait(timeout=timeout + 2)
                logs = container.logs(stdout=True, stderr=True).decode(errors="ignore")
                end = time.time()
                status_code = wait_result.get("StatusCode", 0) if isinstance(wait_result, dict) else 0
                status = "success" if status_code == 0 else "runtime_error"
                return {
                    "status": status,
                    "stdout": logs,
                    "stderr": "" if status == "success" else logs,
                    "execution_time": round(end - start, 3),
                    "returncode": status_code,
                }
            except Exception as e:
                # On timeout or other errors, try to kill and cleanup
                try:
                    container.kill()
                except Exception:
                    pass
                return {"status": "timeout" if "timeout" in str(e).lower() else "error", "message": str(e)}
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        else:
            # Fallback: run directly (dangerous for untrusted code — only use in dev)
            if language == "python":
                cmd = ["python3", dst_code]
                if dst_input:
                    with open(dst_input, "r") as inf:
                        start = time.time()
                        proc = subprocess.run(cmd, stdin=inf, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
                        end = time.time()
                        return {
                            "status": "success" if proc.returncode == 0 else "runtime_error",
                            "stdout": proc.stdout,
                            "stderr": proc.stderr,
                            "execution_time": round(end - start, 3),
                            "returncode": proc.returncode,
                        }
                else:
                    return _run_subprocess(["python3", dst_code], cwd=tmpdir, timeout=timeout)
            elif language == "cpp":
                # compile and run
                return _run_subprocess(["bash", "-lc", f"g++ {dst_code} -O2 -std=c++17 -o {tmpdir}/a.out && {tmpdir}/a.out"], cwd=tmpdir, timeout=timeout)
            elif language == "js":
                return _run_subprocess(["node", dst_code], cwd=tmpdir, timeout=timeout)
            else:
                return {"status": "error", "message": f"unsupported language: {language}"}
    finally:
        # cleanup tmpdir
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
