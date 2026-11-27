@echo off
setlocal
cd /d "%~dp0"
title KPC: prepare a state for the v2 key
echo.
echo   ========================================================
echo     KPC: PREPARE A STATE FOR THE NEW (v2) KEY
echo   ========================================================
echo     It reads the saved layers and the park facts for one state.
echo     It measures which fields carry the parks' ids and names.
echo     It proposes new rows for the rule table. It changes nothing.
echo     It uses only SAVED copies. It never downloads or uploads.
echo     No extra packages are needed.
echo.
set "PY="
rem Python 3.12 first: the GitHub builds run on 3.12.
py -3.12 -c "import sys" >NUL 2>NUL && set "PY=py -3.12"
if not defined PY py -3 -c "import sys" >NUL 2>NUL && set "PY=py -3" && echo     NOTE: Python 3.12 was not found, so the newest Python is used.
if not defined PY python -c "import sys" >NUL 2>NUL && set "PY=python"
if not defined PY (echo     Python was not found. Install Python from python.org first. & pause & exit /b)
set "ST="
set /p "ST=    State (for example SC): "
if not defined ST set "ST=SC"
%PY% -X utf8 kpc_v2_state_prep.py %ST%
echo.
echo   ========================================================
echo     DONE. The report is STATE-PREP-%ST%.txt in the newest
echo     v2-prep-... folder inside the reports folder.
echo     Next: tell Claude "the state prep is done".
echo   ========================================================
echo.
pause
