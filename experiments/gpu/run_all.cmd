@echo off
rem Whole 13B run on the Windows box: env, download, smoke test, train, generate. Logs to C:\hgpu\run.log.
cd /d C:\hgpu
set UV=C:\Users\Vuduc\.local\bin\uv.exe
set PY=C:\hgpu\.venv\Scripts\python.exe
set HF_HUB_DISABLE_PROGRESS_BARS=1
set PYTHONUTF8=1
echo [%date% %time%] setup
if not exist .venv %UV% venv --python 3.12 .venv || exit /b 1
%UV% pip install --python %PY% torch --index-url https://download.pytorch.org/whl/cu128 || exit /b 1
%UV% pip install --python %PY% transformers peft accelerate bitsandbytes safetensors numpy huggingface_hub || exit /b 1
%PY% -c "import torch,bitsandbytes as b;print(torch.__version__,torch.cuda.get_device_name(0),b.__version__)" || exit /b 1
echo [%date% %time%] download
%PY% -c "from huggingface_hub import snapshot_download as s;print(s('allenai/OLMo-2-1124-13B'))" || exit /b 1
echo [%date% %time%] smoke
if not exist out mkdir out
%PY% train13b.py --data data --out out --smoke 5 || exit /b 1
echo [%date% %time%] train
%PY% train13b.py --data data --out out || exit /b 1
echo [%date% %time%] generate
%PY% gen13b.py --data data --out out || exit /b 1
echo [%date% %time%] ALL_DONE
