from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2-1.5B-Instruct",
    local_dir="./qwen_model",
    ignore_patterns=["*.safetensors", "*.bin.index.json", "*.onnx_data", "*.tflite", "*.npz"],
    local_dir_use_symlinks=False
)
