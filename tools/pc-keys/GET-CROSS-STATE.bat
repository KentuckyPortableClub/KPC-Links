@echo off
setlocal
cd /d "%~dp0"
title KPC cross-state pieces (W11)
echo.
echo  KPC cross-state pieces: asks the agencies ONCE for the few park pieces that sit across a state line
echo  (rule W11), one at a time, 5 seconds apart, robots.txt obeyed. Then adds them to this PC's saved copies.
echo  Nothing goes to GitHub and nothing is published. Takes a few minutes.
echo.
set "PY="
py -3 -c "import sys" >NUL 2>NUL && set "PY=py -3"
if not defined PY python -c "import sys" >NUL 2>NUL && set "PY=python"
if not defined PY (echo  Python was not found. Install Python from python.org first. & pause & exit /b)
%PY% -X utf8 kpc_get_cross_state.py %*
echo.
echo  The report is in cross-state-report.txt. Next: run START-HERE.bat and type US.
pause
