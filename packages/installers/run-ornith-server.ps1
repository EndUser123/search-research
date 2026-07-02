# Ornith-1.0-9B (Q4_K_M) on llama.cpp + CUDA 12.8 (RTX 5070, sm_120)
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;$env:PATH"
$bin = "P:\packages\.github_repos\llama.cpp\build\bin"
$model = "P:\packages\models\ornith-1.0-9b-Q4_K_M.gguf"

Write-Host "Starting llama-server with Ornith-1.0-9B on http://127.0.0.1:8080"
Write-Host "Press Ctrl+C to stop."

& "$bin\llama-server.exe" -m "$model" -ngl 99 -c 32768 -t 6 --parallel 1 -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 1024 --reasoning-preserve --jinja --host 127.0.0.1 --port 8080
