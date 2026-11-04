# One-shot status of the 13B run, for checking over SSH.
Get-Date
Get-Process cmd,python -ErrorAction SilentlyContinue | Select Name,Id,StartTime | Format-Table -Auto
$d = Join-Path $env:USERPROFILE '.cache\huggingface\hub\models--allenai--OLMo-2-1124-13B'
if (Test-Path $d) { 'model cache GB: ' + [int]((Get-ChildItem $d -Recurse -File | Measure-Object Length -Sum).Sum / 1GB) }
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
Get-Content C:\hgpu\run.log -Tail 6
