@echo off
setlocal
cd /d "%~dp0"
title KPC: prepare a state for the v2 key
echo.
echo   ========================================================
echo     KPC: PREPARE A STATE FOR THE NEW (v2) KEY
echo   ========================================================
echo     It reads the saved layers and the park facts for one state,
echo     several states, or every state (type US).
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
set /p "ST=    States (for example SC, or MN NY SC, or US for every state): "
if not defined ST set "ST=SC"
%PY% -X utf8 kpc_v2_state_prep.py %ST%
echo.
echo   ========================================================
echo     DONE. The report is in the newest v2-prep-... folder inside
echo     the reports folder: STATE-PREP-SUMMARY.txt for several states,
echo     STATE-PREP-(the state).txt for one.
echo     Next: tell Claude "the state prep is done".
echo   ========================================================
echo.
pause
