#!/usr/bin/env python3
"""ComfyUI + comfyui-mcp installation and deployment script."""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path

def run_cmd(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        print(f"stderr: {result.stderr}")
        return False, result.stderr
    return True, result.stdout

def detect_gpu():
    """Detect GPU type and return PyTorch index URL."""
    ret, stdout, _ = run_cmd("nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null", check=False)
    if ret and stdout.strip():
        print(f"[INFO] Detected NVIDIA GPU: {stdout.strip()}")
        return "nvidia", "https://download.pytorch.org/whl/cu126"
    
    if platform.system() == "Linux":
        ret, stdout, _ = run_cmd("rocm-smi --show-gpu-name 2>/dev/null", check=False)
        if ret and stdout.strip():
            print(f"[INFO] Detected AMD GPU: {stdout.strip()}")
            return "amd", "https://download.pytorch.org/whl/rocm6.3"
    
    if platform.system() == "Darwin" and platform.processor() == "arm":
        print("[INFO] Detected Apple Silicon (M-series)")
        return "apple", None
    
    print("[INFO] No GPU detected, using CPU mode")
    return "cpu", None

def install_comfyui(target_path):
    """Install ComfyUI to the specified path."""
    target = Path(target_path).resolve()
    
    if target.exists():
        print(f"[INFO] ComfyUI already installed at: {target}")
        return True
    
    print(f"[INFO] Installing ComfyUI to: {target}")
    
    success, _ = run_cmd(f"git clone https://github.com/comfyanonymous/ComfyUI.git {target}")
    if not success:
        return False
    
    venv_path = target / "venv"
    success, _ = run_cmd(f"python3 -m venv {venv_path}")
    if not success:
        return False
    
    gpu_type, pytorch_index = detect_gpu()
    pip_path = venv_path / "bin" / "pip"
    
    print("[INFO] Installing PyTorch...")
    if pytorch_index:
        success, _ = run_cmd(f"{pip_path} install torch torchvision torchaudio --index-url {pytorch_index}", cwd=target)
    else:
        success, _ = run_cmd(f"{pip_path} install torch torchvision torchaudio", cwd=target)
    
    if not success:
        return False
    
    print("[INFO] Installing ComfyUI dependencies...")
    success, _ = run_cmd(f"{pip_path} install -r requirements.txt", cwd=target)
    
    print(f"[SUCCESS] ComfyUI installed at: {target}")
    return True

def configure_model_paths(comfyui_path, models_path):
    """Configure extra_model_paths.yaml."""
    config_file = Path(comfyui_path) / "extra_model_paths.yaml"
    
    config_content = f"""# Extra model paths for MiniMax-H3 and other models
external_models:
    base_path: {models_path}/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    loras: loras/
    vae: vae/
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"[INFO] Model paths configured: {config_file}")
    return True

def install_comfyui_mcp(target_path):
    """Install comfyui-mcp."""
    target = Path(target_path).resolve()
    
    if target.exists():
        print(f"[INFO] comfyui-mcp already installed at: {target}")
        return True
    
    print(f"[INFO] Installing comfyui-mcp to: {target}")
    
    success, _ = run_cmd(f"git clone https://github.com/artokun/comfyui-mcp.git {target}")
    if not success:
        return False
    
    success, _ = run_cmd("npm install", cwd=target)
    if not success:
        return False
    
    success, _ = run_cmd("npm run build", cwd=target)
    if not success:
        return False
    
    print(f"[SUCCESS] comfyui-mcp installed at: {target}")
    return True

def install_dependencies():
    """Install required system dependencies."""
    print("[INFO] Checking system dependencies...")
    
    # Check for gcc (needed for Triton)
    ret, _ = run_cmd("which gcc", check=False)
    if not ret:
        print("[INFO] Installing gcc...")
        if platform.system() == "Linux":
            run_cmd("apt-get update && apt-get install -y gcc g++", check=False)
    
    print("[SUCCESS] Dependencies ready")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python install_comfyui_mcp.py <comfyui_path> <mcp_path> [models_path]")
        print("Example: python install_comfyui_mcp.py /workspace/ComfyUI /workspace/comfyui-mcp /workspace/models")
        sys.exit(1)
    
    comfyui_path = sys.argv[1]
    mcp_path = sys.argv[2]
    models_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("=" * 50)
    print("ComfyUI + comfyui-mcp Deployment")
    print("=" * 50)
    
    # Install dependencies
    install_dependencies()
    
    # Install ComfyUI
    if not install_comfyui(comfyui_path):
        print("[ERROR] ComfyUI installation failed")
        sys.exit(1)
    
    # Configure model paths
    if models_path:
        configure_model_paths(comfyui_path, models_path)
    
    # Install comfyui-mcp
    if not install_comfyui_mcp(mcp_path):
        print("[ERROR] comfyui-mcp installation failed")
        sys.exit(1)
    
    print("=" * 50)
    print("[SUCCESS] Deployment complete!")
    print("=" * 50)
    print(f"\nComfyUI: {comfyui_path}")
    print(f"comfyui-mcp: {mcp_path}")
    print(f"\nTo start:")
    print(f"  1. Start ComfyUI: cd {comfyui_path} && source venv/bin/activate && python main.py --listen 0.0.0.0")
    print(f"  2. Test MCP: cd {mcp_path} && COMFYUI_HOST=127.0.0.1 COMFYUI_PORT=8188 node dist/index.js")

if __name__ == "__main__":
    main()
