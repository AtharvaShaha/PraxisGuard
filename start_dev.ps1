# PowerShell wrapper to run the Python dev runner from project root.
# Usage: Open PowerShell in project root and run: .\start_dev.ps1

& "$PSScriptRoot\env\Scripts\Activate.ps1"
python -u "$PSScriptRoot\dev_runner.py"
