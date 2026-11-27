@echo off
setlocal
cd /d "%~dp0"
title KPC: build the v2 keys
echo.
echo   ========================================================
echo     KPC: BUILD THE NEW (v2) KEYS ON THIS PC
echo   ========================================================
echo     It builds the new key for every state or province you pick.
echo     One at a time. Each one is built twice, to check the locks.
echo     Where you have an old key it compares with it. Where not, it
echo     reports the area on its own. The old keys are never touched.
echo     It uses only the SAVED copies of the layers.
echo     It never downloads, never uploads, never publishes.
echo     No extra packages are needed.
echo.
set "PY="
rem Python 3.12 first: the GitHub builds run on 3.12.
py -3.12 -c "import sys" >NUL 2>NUL && set "PY=py -3.12"
if not defined PY py -3 -c "import sys" >NUL 2>NUL && set "PY=py -3" && echo     NOTE: Python 3.12 was not found, so the newest Python is used.
if not defined PY python -c "import sys" >NUL 2>NUL && set "PY=python"
if not defined PY (echo     Python was not found. Install Python from python.org first. & pause & exit /b)
echo     Type areas with a space between them: MN NY, or CA-ON.
echo     Type US for every state, CA for every province, ALL for both.
echo     Or just press Enter for MN NY. A big run takes a while.
echo.
set "ST="
set /p "ST=    Areas (for example MN NY, or CA-ON, or US, CA, ALL): "
if not defined ST set "ST=MN NY"
%PY% -X utf8 kpc_test_v2.py build %ST%
echo.
echo   ========================================================
echo     DONE. The report is V2-BUILD-SUMMARY.txt in the newest
echo     folder inside v2-keys (beside the reports folder).
echo     The built keys are in its keys folder. Nothing was published.
echo     Next: tell Claude "the v2 build is done".
echo   ========================================================
echo.
pause
