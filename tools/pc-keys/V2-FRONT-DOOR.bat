@echo off
setlocal
cd /d "%~dp0"
title KPC: the v2 key, step by step
rem 27 Nov 2026. A DRAFT front door. It only calls buttons that already exist and says so when one is missing.
rem It starts nothing by itself: a step starts only when you type its number.
set "B1=C:\KPC\3-MAP-STORE-US-CA\LAYER-RECORDS.bat"
set "B2=C:\KPC\6-TOOLS\PAGE-READER\PAGE-READER.bat"
set "B3=C:\KPC\5-ANSWER-KEY-TEST\V2-STATE-PREP.bat"
set "B4=C:\KPC\5-ANSWER-KEY-TEST\V2-BUILD.bat"
:menu
set "S1=found"
set "S2=found"
set "S3=found"
set "S4=found"
if not exist "%B1%" set "S1=MISSING"
if not exist "%B2%" set "S2=MISSING"
if not exist "%B3%" set "S3=MISSING"
if not exist "%B4%" set "S4=MISSING"
echo.
echo   ========================================================
echo     KPC: THE NEW (v2) KEY, STEP BY STEP
echo   ========================================================
echo     Do the steps in this order. Nothing starts until you type
echo     a number. Each step is its own button and asks its own
echo     questions.
echo.
echo     1  Store room    the layer files from the agencies     %S1%
echo     2  Page reader   the park pages, for the park facts    %S2%
echo     3  State prep    check a state before you build it     %S3%
echo     4  Build         make the v2 keys                      %S4%
echo.
echo     In steps 1 and 2, pick 1 first: it only shows the status.
echo     Only the store room and the page reader go to the internet,
echo     and only when you pick their download choice (3).
echo     After step 2 the park facts are rebuilt. That has no button
echo     yet: tell Claude "the page reader is done".
echo.
set "PICK="
set /p "PICK=    Type 1, 2, 3 or 4 (or just press Enter to leave): "
if not defined PICK goto :end
if "%PICK%"=="1" goto :step1
if "%PICK%"=="2" goto :step2
if "%PICK%"=="3" goto :step3
if "%PICK%"=="4" goto :step4
echo.
echo     That is not on the list. Type 1, 2, 3 or 4.
goto :menu
:step1
set "NAME=the store room"
set "TARGET=%B1%"
goto :go
:step2
set "NAME=the page reader"
set "TARGET=%B2%"
goto :go
:step3
set "NAME=the state prep"
set "TARGET=%B3%"
goto :go
:step4
set "NAME=the build"
set "TARGET=%B4%"
goto :go
:go
if not exist "%TARGET%" goto :missing
echo.
echo     Starting %NAME%. It will ask its own questions.
call "%TARGET%"
cd /d "%~dp0"
echo.
echo     Back at the step list.
goto :menu
:missing
echo.
echo     %NAME% is MISSING. This file was not found:
echo       %TARGET%
echo     Nothing was started. Tell Claude.
goto :menu
:end
echo.
echo     Closed. Nothing else was started.
echo.
pause
