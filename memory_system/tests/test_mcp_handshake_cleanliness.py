import subprocess
import time
import os
import json
import sys
import select

def test_mcp_handshake():
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    p = subprocess.Popen(
        ["uv", "run", "--with", "mcp", "--with", "httpx", "-m", "memory_system.mcp_server"],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait a bit for initialization, but since models are lazy it should be fast
    time.sleep(1)

    # Check for any unexpected initial output (there should be none on stdout)
    initial_stdout = ""
    while True:
        r, _, _ = select.select([p.stdout], [], [], 0.1)
        if r:
            line = p.stdout.readline()
            initial_stdout += line
        else:
            break

    if initial_stdout:
        print(f"FAILED: Unexpected initial STDOUT: {repr(initial_stdout)}")
        p.terminate()
        sys.exit(1)

    # 1. Send Initialize Request
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    p.stdin.write(json.dumps(init_req) + "\n")
    p.stdin.flush()

    # Wait for response
    time.sleep(1)

    response_line = p.stdout.readline()
    try:
        resp = json.loads(response_line)
        if "result" in resp and "serverInfo" in resp["result"]:
            print("SUCCESS: Handshake initialized properly.")
        else:
            print(f"FAILED: Malformed initialization response: {resp}")
            p.terminate()
            sys.exit(1)
    except Exception as e:
        print(f"FAILED: JSON parse error on stdout: {repr(response_line)}")
        p.terminate()
        sys.exit(1)

    # 2. Send tools/list Request
    tools_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    p.stdin.write(json.dumps(tools_req) + "\n")
    p.stdin.flush()

    time.sleep(1)

    response_line = p.stdout.readline()
    try:
        resp = json.loads(response_line)
        if "result" in resp and "tools" in resp["result"]:
            tools = resp["result"]["tools"]
            print(f"SUCCESS: tools/list returned {len(tools)} tools.")
        else:
            print(f"FAILED: Malformed tools/list response: {resp}")
            p.terminate()
            sys.exit(1)
    except Exception as e:
        print(f"FAILED: JSON parse error on tools/list response: {repr(response_line)}")
        p.terminate()
        sys.exit(1)

    p.terminate()
    print("ALL TESTS PASSED: Clean stdout and valid JSON-RPC via uv run.")

if __name__ == "__main__":
    test_mcp_handshake()
