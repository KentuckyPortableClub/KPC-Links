@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  INSTALL THE TWO PYTHON PACKAGES THE 2-FERS NEED (once^)
echo ----------------------------------------------------------
echo  numpy and opencv-python-headless: the same two the club's
echo  GitHub runs install. Needs the internet. Safe to run again.
echo ==========================================================
echo.
%PY% -m pip install --upgrade pip
%PY% -m pip install numpy opencv-python-headless
echo.
echo --- checking they load:
%PY% -c "import numpy, cv2; print('numpy', numpy.__version__, '/ opencv', cv2.__version__, ': READY')" || (echo STOPPED: they did not load. Send a picture of this window.& pause & exit /b 2)
echo.
echo ==========================================================
echo  Done. Now run 0-CHECK-SETUP.bat, then RUN-ALL.bat.
echo ==========================================================
pause
