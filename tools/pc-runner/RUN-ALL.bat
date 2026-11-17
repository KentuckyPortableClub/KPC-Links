@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  RUN EVERY STEP, IN ORDER (US AND CANADA)
echo ----------------------------------------------------------
echo  1 get the code, 0 check the setup, 2 run the 2-fers,
echo  4 check and write the summary. The world step (3) is
echo  separate, because its results are club room only.
echo ==========================================================
echo.
call 1-GET-CODE.bat
%PY% tools\kpc_pc_run.py check || (echo STOPPED at the setup check.& pause & exit /b 2)
%PY% tools\kpc_pc_run.py run --minutes 350
%PY% tools\kpc_pc_run.py summary
echo.
pause
