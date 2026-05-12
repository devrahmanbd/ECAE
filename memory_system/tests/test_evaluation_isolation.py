import pytest
import json
from memory_system.cli_parser import parse_and_route_ecae_command
from memory_system.services.memory_service import search_memory
from memory_system.db.qdrant_client import init_collection

def setup_module(module):
    init_collection()

def test_evaluation_isolation():
    # Run evaluation
    res_str = parse_and_route_ecae_command("/ecae evaluate")
    res = json.loads(res_str)

    assert "metrics" in res
    assert "governance" in res

    # Assert it was written to evaluation namespace
    eval_res = search_memory("ECAE Learning Evaluation", namespace="evaluation")
    assert len(eval_res) > 0

    # Assert it did NOT pollute production namespace
    prod_res = search_memory("ECAE Learning Evaluation", namespace="production")
    filtered_prod = [r for r in prod_res if "ECAE Learning Evaluation" in r.text]
    assert len(filtered_prod) == 0
