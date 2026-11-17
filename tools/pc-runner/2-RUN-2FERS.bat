@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  STEP 2: RUN THE 2-FERS FOR US AND CANADA
echo ----------------------------------------------------------
echo  Runs the club's own 2-fer bot on this PC, reading your
echo  outline store. It makes NO internet request at all.
echo  It stops when the time runs out; run it again to carry on
echo  with the areas it did not reach.
echo  Nothing is uploaded. Nothing is pushed.
echo ==========================================================
echo.
set /p MINS=How many minutes may it run in total (press Enter for 350)? 
if "%MINS%"=="" set MINS=350
set /p AREAS=Which areas (e.g. US-RI,US-DE - press Enter for every area)? 
echo.
if "%AREAS%"=="" (%PY% tools\kpc_pc_run.py run --minutes %MINS%) else (%PY% tools\kpc_pc_run.py run --minutes %MINS% --areas "%AREAS%")
echo.
echo ==========================================================
echo  Now run 4-CHECK-AND-SUMMARY.bat.
echo ==========================================================
pause
