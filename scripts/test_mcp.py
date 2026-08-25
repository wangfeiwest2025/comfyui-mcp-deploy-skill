#!/usr/bin/env python3
"""Test comfyui-mcp connection and functionality."""

import subprocess
import json
import sys
import time

def test_mcp_connection(mcp_path, comfyui_host="127.0.0.1", comfyui_port="8188"):
    """Test MCP server connection."""
    print("[INFO] Testing comfyui-mcp connection...")
    
    # Test initialize
    init_request = json.dumps({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        },
        "id": 1
    })
    
    env = f"COMFYUI_HOST={comfyui_host} COMFYUI_PORT={comfyui_port}"
    result = subprocess.run(
        f'{env} echo \'{init_request}\' | node {mcp_path}/dist/index.js',
        shell=True, capture_output=True, text=True, timeout=30
    )
    
    if result.returncode != 0:
        print(f"[ERROR] MCP initialization failed: {result.stderr}")
        return False
    
    # Parse response
    for line in result.stdout.strip().split('\n'):
        if line.startswith('{'):
            response = json.loads(line)
            if "result" in response:
                server_info = response["result"].get("serverInfo", {})
                print(f"[SUCCESS] Connected to comfyui-mcp v{server_info.get('version', 'unknown')}")
                return True
    
    print("[ERROR] Invalid MCP response")
    return False

def test_tools_list(mcp_path, comfyui_host="127.0.0.1", comfyui_port="8188"):
    """Test tools/list endpoint."""
    print("[INFO] Fetching available tools...")
    
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    })
    
    env = f"COMFYUI_HOST={comfyui_host} COMFYUI_PORT={comfyui_port}"
    result = subprocess.run(
        f'{env} echo \'{request}\' | node {mcp_path}/dist/index.js',
        shell=True, capture_output=True, text=True, timeout=30
    )
    
    for line in result.stdout.strip().split('\n'):
        if line.startswith('{') and '"result"' in line:
            response = json.loads(line)
            tools = response.get("result", {}).get("tools", [])
            print(f"[SUCCESS] Available tools: {len(tools)}")
            tool_names = [t["name"] for t in tools[:10]]
            print(f"[INFO] Sample tools: {', '.join(tool_names)}...")
            return True
    
    return False

def test_system_stats(mcp_path, comfyui_host="127.0.0.1", comfyui_port="8188"):
    """Test get_system_stats tool."""
    print("[INFO] Testing system stats...")
    
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "get_system_stats", "arguments": {"action": "health"}},
        "id": 3
    })
    
    env = f"COMFYUI_HOST={comfyui_host} COMFYUI_PORT={comfyui_port}"
    result = subprocess.run(
        f'{env} echo \'{request}\' | node {mcp_path}/dist/index.js',
        shell=True, capture_output=True, text=True, timeout=30
    )
    
    for line in result.stdout.strip().split('\n'):
        if line.startswith('{') and '"result"' in line:
            response = json.loads(line)
            content = response.get("result", {}).get("content", [])
            if content:
                text = content[0].get("text", "")
                # Extract key info
                for info_line in text.split('\n')[:10]:
                    if info_line.strip():
                        print(f"  {info_line}")
                print("[SUCCESS] System stats retrieved")
                return True
    
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_mcp.py <mcp_path> [comfyui_host] [comfyui_port]")
        sys.exit(1)
    
    mcp_path = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = sys.argv[3] if len(sys.argv) > 3 else "8188"
    
    print("=" * 50)
    print("comfyui-mcp Test Suite")
    print("=" * 50)
    
    tests = [
        ("Connection", lambda: test_mcp_connection(mcp_path, host, port)),
        ("Tools List", lambda: test_tools_list(mcp_path, host, port)),
        ("System Stats", lambda: test_system_stats(mcp_path, host, port)),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 50)
    
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    main()
