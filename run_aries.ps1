Write-Host "Starting A.R.I.E.S. - Autonomous Reasoning & Interaction Executive System" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Run A.R.I.E.S.
python main.py

# Keep window open if there's an error
Read-Host "Press Enter to continue..."
