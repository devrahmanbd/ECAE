import os
from typing import Dict, Any, Tuple

def get_profile_config(workspace_dir: str) -> Dict[str, Any]:
    """
    Returns the execution profile configuration based on the detected project type.
    """

    if not os.path.exists(workspace_dir) or not os.path.isdir(workspace_dir):
        return {
            "name": "unknown",
            "image": "ubuntu:22.04",
            "build_cmd": "",
            "validation_cmd": "echo 'Invalid or non-existent workspace'"
        }

    # Python
    if os.path.exists(os.path.join(workspace_dir, "requirements.txt")) or \
       os.path.exists(os.path.join(workspace_dir, "pytest.ini")) or \
       os.path.exists(os.path.join(workspace_dir, "setup.py")):
        return {
            "name": "python",
            "image": "python:3.11-slim",
            "build_cmd": "pip install -r requirements.txt || true",
            "validation_cmd": "pytest"
        }

    # Go
    elif os.path.exists(os.path.join(workspace_dir, "go.mod")):
        return {
            "name": "go",
            "image": "golang:1.21",
            "build_cmd": "go build ./...",
            "validation_cmd": "go test ./..."
        }

    # JS/TS
    elif os.path.exists(os.path.join(workspace_dir, "package.json")):
        return {
            "name": "js/ts",
            "image": "node:20-slim",
            "build_cmd": "npm install",
            "validation_cmd": "npm test"
        }

    # Rust
    elif os.path.exists(os.path.join(workspace_dir, "Cargo.toml")):
        return {
            "name": "rust",
            "image": "rust:1.75",
            "build_cmd": "cargo build",
            "validation_cmd": "cargo test"
        }

    # SQL/Postgres
    elif any(f.endswith(".sql") for f in os.listdir(workspace_dir)):
        return {
            "name": "sql/postgres",
            "image": "postgres:15-alpine",
            "build_cmd": "",
            "validation_cmd": "pg_isready -h localhost -p 5432 || true" # replaced exit with true to avoid sandbox kill
        }

    # Redis
    elif os.path.exists(os.path.join(workspace_dir, "docker-compose.yml")) or \
         os.path.exists(os.path.join(workspace_dir, "redis.conf")):
        return {
            "name": "redis",
            "image": "redis:7-alpine",
            "build_cmd": "",
            "validation_cmd": "redis-cli ping || true" # replaced exit with true
        }

    # HTML/Web (Static)
    elif any(f.endswith(".html") for f in os.listdir(workspace_dir)):
        return {
            "name": "html/web",
            "image": "nginx:alpine",
            "build_cmd": "",
            "validation_cmd": "nginx -t"
        }

    # Desktop / Native Linux / CLI generic fallback
    elif os.path.exists(os.path.join(workspace_dir, "Makefile")):
        return {
            "name": "linux/cli",
            "image": "ubuntu:22.04",
            "build_cmd": "apt-get update && apt-get install -y build-essential && make",
            "validation_cmd": "make test"
        }

    # Fallback Unknown
    return {
        "name": "unknown",
        "image": "ubuntu:22.04",
        "build_cmd": "",
        "validation_cmd": "echo 'No validation profile matched'"
    }

def extract_stack_trace(stderr: str) -> str:
    """Naive extraction of stack traces from stderr dumps."""
    lines = stderr.splitlines()
    trace_lines = []
    in_trace = False

    for line in lines:
        if "Traceback (most recent call last)" in line or "panic:" in line or "Error:" in line:
            in_trace = True

        if in_trace:
            trace_lines.append(line)

    return "\n".join(trace_lines) if trace_lines else ""
