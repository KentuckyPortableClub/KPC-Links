@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  STEP 3: RUN THE WORLD 2-FERS (CLUB ROOM ONLY)
echo ----------------------------------------------------------
echo  The same bot, on your WORLD outline store. World 2-fers
echo  are CLUB ROOM ONLY: every file this step writes goes to
echo  the PRIVATE folder and must never be uploaded anywhere.
echo  On GitHub the world areas stay switched OFF; this step
echo  switches them on for THIS PC only.
echo  It makes NO internet request at all.
echo ==========================================================
echo.
set /p MINS=How many minutes may it run in total (press Enter for 350)? 
if "%MINS%"=="" set MINS=350
set /p AREAS=Which countries (e.g. W-GB,W-JP - press Enter for every one your world store holds)? 
echo.
if "%AREAS%"=="" (%PY% tools\kpc_pc_run.py run --world --minutes %MINS%) else (%PY% tools\kpc_pc_run.py run --world --minutes %MINS% --areas "%AREAS%")
echo.
echo ==========================================================
echo  The world results are in the PRIVATE folder. CLUB ROOM
echo  ONLY: do not put them in a repo and do not send them on.
echo ==========================================================
pause
