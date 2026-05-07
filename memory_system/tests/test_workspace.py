import os
import json
import pytest
import shutil
from memory_system.services.workspace_service import detect_workspace, get_execution_profile, init_project

@pytest.fixture
def temp_workspace(tmp_path):
    workspace = tmp_path / "my_project"
    workspace.mkdir()
    yield workspace
    if workspace.exists():
        shutil.rmtree(workspace)

def test_detect_workspace(temp_workspace):
    # Setup marker
    (temp_workspace / "requirements.txt").write_text("pytest\n")
    subfolder = temp_workspace / "src" / "module"
    subfolder.mkdir(parents=True)

    root = detect_workspace(str(subfolder))
    assert root == str(temp_workspace)

def test_get_execution_profile_python(temp_workspace):
    (temp_workspace / "requirements.txt").write_text("pytest\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "python"
    assert profile.validation_command == "pytest"

def test_get_execution_profile_go(temp_workspace):
    (temp_workspace / "go.mod").write_text("module test\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "go"
    assert profile.validation_command == "go test ./..."

def test_get_execution_profile_js(temp_workspace):
    (temp_workspace / "package.json").write_text("{}\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "js/ts"
    assert profile.validation_command == "npm test"

def test_get_execution_profile_sql(temp_workspace):
    (temp_workspace / "schema.sql").write_text("SELECT 1;\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "sql/postgres"
    assert profile.validation_command == "migration validation command"

def test_get_execution_profile_redis(temp_workspace):
    (temp_workspace / "redis.conf").write_text("port 6379\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "redis"
    assert profile.validation_command == "redis health check"

def test_get_execution_profile_redis_compose(temp_workspace):
    (temp_workspace / "docker-compose.yml").write_text("services:\n  redis:\n    image: redis\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "redis"
    assert profile.validation_command == "redis health check"

def test_get_execution_profile_compose_unknown(temp_workspace):
    (temp_workspace / "docker-compose.yml").write_text("services:\n  web:\n    image: nginx\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "unknown"

def test_get_execution_profile_html(temp_workspace):
    (temp_workspace / "index.html").write_text("<html></html>\n")
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "html/web"
    assert profile.validation_command == "smoke test"

def test_get_execution_profile_unknown(temp_workspace):
    profile = get_execution_profile(str(temp_workspace))
    assert profile.language == "unknown"

def test_init_project(temp_workspace):
    (temp_workspace / "requirements.txt").write_text("pytest\n")
    metadata = init_project(str(temp_workspace))

    assert metadata["project_root"] == str(temp_workspace)
    assert metadata["language_profile"] == "python"
    assert metadata["initialized"] is True
