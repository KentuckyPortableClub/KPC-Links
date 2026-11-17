@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  STEP 4: CHECK THE RESULT AND WRITE THE SUMMARY
echo ----------------------------------------------------------
echo  Copies the files a GitHub run would push into
echo  RESULTS\to-kpc-data, runs the club's push check over
echo  them, compares them with today's live 2-fers (never
echo  worse) and writes RESULTS\SUMMARY.txt.
echo  Nothing is uploaded and nothing is pushed.
echo ==========================================================
echo.
%PY% tools\kpc_pc_run.py summary
echo.
pause
