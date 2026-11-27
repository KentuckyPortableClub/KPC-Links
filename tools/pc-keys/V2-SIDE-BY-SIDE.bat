@echo off
setlocal
cd /d "%~dp0"
title KPC: test the v2 key
echo.
echo   ========================================================
echo     KPC: TEST THE NEW (v2) KEY SIDE BY SIDE WITH THE OLD ONE
echo   ========================================================
echo     It builds the new key for the states you pick.
echo     Then it compares it with your last key test.
echo     It does not build the old key again, so it takes seconds.
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
echo     Type the states with a space between them.
echo     Or just press Enter for MN NY SC.
echo.
set "ST="
set /p "ST=    States (for example MN NY SC): "
if not defined ST set "ST=MN NY SC"
%PY% -X utf8 kpc_test_v2.py %ST%
echo.
echo   ========================================================
echo     DONE. The report is V2-SCORECARD.txt in the newest
echo     v2-... folder inside the reports folder.
echo     Next: tell Claude "the v2 test is done".
echo   ========================================================
echo.
pause
