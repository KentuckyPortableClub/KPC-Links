@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  STEP 0: CHECK THE SETUP
echo ----------------------------------------------------------
echo  Looks at your folders, the shipped club code and the two
echo  checkouts, and prints the commits and rules hashes it
echo  would use. Nothing is run and nothing is changed.
echo ==========================================================
echo.
%PY% tools\kpc_pc_run.py check
echo.
echo ==========================================================
echo  If it says ALL READY, go to step 2 (US and Canada).
echo  If it asks for the code, run 1-GET-CODE.bat first.
echo ==========================================================
pause
