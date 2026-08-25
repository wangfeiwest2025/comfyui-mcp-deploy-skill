---
name: comfyui-mcp-deploy
description: Deploy and manage ComfyUI with comfyui-mcp MCP server for AI image/video generation. Use when installing ComfyUI, setting up comfyui-mcp, configuring model paths, starting the server, or generating images/videos through MCP. Handles GPU detection, dependency installation, and MiniMax-H3 video generation workflows.
---

# ComfyUI + comfyui-mcp Deployment

## Overview

Deploy ComfyUI with the comfyui-mcp MCP server for AI-powered image and video generation. Supports MiniMax-H3 video generation and other ComfyUI workflows.

## Quick Start

```bash
# Install both ComfyUI and comfyui-mcp
python /root/.qoder/skills/comfyui-mcp-deploy/scripts/install_comfyui_mcp.py /workspace/ComfyUI /workspace/comfyui-mcp /workspace/models
```

## Step-by-Step Deployment

### 1. Install ComfyUI

ComfyUI must be installed first with GPU-appropriate PyTorch.

```bash
# Run the installer
python /root/.qoder/skills/comfyui-mcp-deploy/scripts/install_comfyui_mcp.py <comfyui_path> <mcp_path> [models_path]
```

The installer:
- Detects GPU type (NVIDIA/AMD/Apple Silicon/CPU)
- Installs correct PyTorch version
- Creates virtual environment
- Installs all dependencies

### 2. Configure Model Paths

If models are stored externally, configure `extra_model_paths.yaml`:

```yaml
# <comfyui_path>/extra_model_paths.yaml
external_models:
    base_path: /workspace/models/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    loras: loras/
    vae: vae/
```

### 3. Start ComfyUI

```bash
cd /workspace/ComfyUI
source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188
```

### 4. Test MCP Connection

```bash
python /root/.qoder/skills/comfyui-mcp-deploy/scripts/test_mcp.py /workspace/comfyui-mcp
```

## MiniMax-H3 Video Generation

MiniMax-H3 is a video generation model that requires specific nodes and workflow.

### Required Models

- **Diffusion Model**: `minimax_h3_fl2va_int8_convrot.safetensors` (~34GB)
- **Text Encoder**: `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (~27GB)
- **Video VAE**: `minimax_h3_video_vae_fp16.safetensors`
- **Audio VAE**: `minimax_h3_audio_vae_fp32.safetensors`

### Workflow Structure

```
MiniMaxH3Loader → MiniMaxH3EncoderLoader → MiniMaxH3VAELoader
                                            ↓
MiniMaxH3SimplePrompt → MiniMaxH3Conditioning
                                            ↓
MiniMaxH3KSampler → MiniMaxH3Decode → SaveImage
```

### Example Workflow (JSON)

```json
{
  "1": {"class_type": "MiniMaxH3Loader", "inputs": {"model_name": "minimax_h3_fl2va_int8_convrot.safetensors"}},
  "2": {"class_type": "MiniMaxH3EncoderLoader", "inputs": {"model_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors", "use_final_norm": false, "group_size": 2}},
  "3": {"class_type": "MiniMaxH3VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors", "audio_vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
  "4": {"class_type": "MiniMaxH3SimplePrompt", "inputs": {"text": "A sunset over ocean", "mode": "T2VA", "total_duration": 5.0, "ratio": "16:9"}},
  "5": {"class_type": "MiniMaxH3Conditioning", "inputs": {"text_encoder": ["2", 0], "av_encoder": ["3", 0], "prompt": ["4", 0], "width": 1344, "height": 768}},
  "6": {"class_type": "MiniMaxH3KSampler", "inputs": {"model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "latent": ["5", 2], "seed": 42, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler_name": "normal", "shift_video": 1.0, "shift_audio": 1.0, "denoise": 1.0, "use_adaln_cache": true, "adaln_prebake_batch": 1}},
  "7": {"class_type": "MiniMaxH3Decode", "inputs": {"latent": ["6", 0], "av_encoder": ["3", 0]}},
  "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "video"}}
}
```

### Submit via API

```bash
curl -X POST http://127.0.0.1:8188/prompt -H "Content-Type: application/json" -d '{"prompt": <workflow_json>}'
```

### Monitor Progress

```bash
curl http://127.0.0.1:8188/history/<prompt_id>
```

## Troubleshooting

### Missing C Compiler

Triton requires gcc for JIT compilation:

```bash
apt-get update && apt-get install -y gcc g++
```

### Port Already in Use

```bash
pkill -f "python main.py"
```

### Database Lock Error

Delete the lock file:

```bash
rm /workspace/ComfyUI/user/comfyui.db-wal
```

## Resources

- `scripts/install_comfyui_mcp.py` - Full deployment script
- `scripts/test_mcp.py` - MCP connection test
