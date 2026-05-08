import pytest
import os
import tempfile
import json
from memory_system.models.schemas import MemoryMetadata, EvidencePacket
from memory_system.services.memory_service import assemble_evidence, store_memory
from memory_system.db.qdrant_client import init_collection
from memory_system.services.workspace_service import init_project
from memory_system.mcp_server import call_tool

def setup_module(module):
    init_collection()

def test_evidence_assembly():
    with tempfile.TemporaryDirectory() as tmpdir:
        init_project(tmpdir)
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def target(): pass\n")

        store_memory("task target success", MemoryMetadata(outcome="success", critique="Great job"))
        store_memory("task target failure", MemoryMetadata(outcome="failure", critique="Failed badly"))

        packet = assemble_evidence("target", workspace_dir=tmpdir)

        assert isinstance(packet, EvidencePacket)
        assert packet.task == "target"
        assert len(packet.recent_successes) >= 1
        assert len(packet.recent_failures) >= 1
        assert len(packet.critique_records) >= 2

@pytest.mark.asyncio
async def test_mcp_composite_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        import memory_system.mcp_server as ms

        def mock_detect(*args): return tmpdir
        ms.detect_workspace = mock_detect

        res = await call_tool("assemble_evidence", {"task": "target"})
        assert len(res) == 1

        payload = json.loads(res[0].text)
        assert "task" in payload
        assert "recent_successes" in payload
        assert "recent_failures" in payload
