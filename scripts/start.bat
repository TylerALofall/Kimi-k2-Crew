@echo off
echo ========================================
echo MCP Multi-Model Orchestrator
echo ========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Install Ollama from https://ollama.ai
echo 2. Run: ollama pull qwen3
echo 3. Run: ollama pull llama2-uncensored
echo 4. Run: ollama pull llava
echo 5. Start Ollama: ollama serve
echo 6. Run the GUI: python gui_controller.py
echo.
echo Starting GUI in 3 seconds...
timeout /t 3 /nobreak > nul

python gui_controller.py

pause
