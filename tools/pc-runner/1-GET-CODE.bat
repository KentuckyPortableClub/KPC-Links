@echo off
setlocal
cd /d "%~dp0"
set PY=python
where %PY% >nul 2>nul || set PY=py
echo ==========================================================
echo  STEP 1: GET THE CLUB CODE (needs the internet, once)
echo ----------------------------------------------------------
echo  Downloads two things into the repos\ folder beside this
echo  file:
echo    repos\KPC-Links       the 2-fer code and the answer keys
echo                          at the PINNED commit in pins.json
echo    repos\KPC-Data-data   the data folder the 2-fer bot reads
echo                          and writes (data\ only, no code)
echo  Everything else this runner needs is already in the zip.
echo  Nothing is uploaded. Run it again any time: it just
echo  updates the two folders.
echo ==========================================================
echo.
where git >nul 2>nul || (echo STOPPED: Git for Windows is not installed. Get it from https://git-scm.com/download/win and run this again.& pause & exit /b 2)
for /f "tokens=2 delims=:, " %%A in ('findstr /c:"kpc_links_commit" pins.json') do set LC=%%~A
for /f "tokens=2 delims=:, " %%A in ('findstr /c:"kpc_data_commit" pins.json') do set DC=%%~A
echo KPC-Links pinned commit: %LC%
echo KPC-Data  pinned commit: %DC%
echo.
if not exist repos mkdir repos
if not exist "repos\KPC-Links\.git" (
  echo --- first download of KPC-Links (this takes a few minutes^)
  git clone --no-checkout -c core.autocrlf=false -c core.eol=lf https://github.com/KentuckyPortableClub/KPC-Links "repos\KPC-Links" || (echo STOPPED: the download failed.& pause & exit /b 2)
)
rem Nov 16: LINE ENDINGS. Git for Windows writes CRLF by default. The answer-key rules hash is worked out from the
rem BYTES of the rule files, so a CRLF checkout gives a different hash than the club's builds and the 2-fer key gate
rem then refuses every area. Keep this checkout exactly as the repository holds it: LF.
git -C "repos\KPC-Links" config core.autocrlf false
git -C "repos\KPC-Links" config core.eol lf
git -C "repos\KPC-Links" fetch --all --tags || (echo STOPPED: could not fetch KPC-Links.& pause & exit /b 2)
rem an older folder on this PC may already hold CRLF files: forget what git thinks is on disk, then lay them down again
git -C "repos\KPC-Links" rm --cached -r -q . >nul 2>nul
git -C "repos\KPC-Links" checkout --force %LC% || (echo STOPPED: that commit is not in KPC-Links yet. Has the branch been pushed?& pause & exit /b 2)
echo.
if not exist "repos\KPC-Data-data\.git" (
  echo --- first download of the KPC-Data DATA folder (this takes a few minutes^)
  git clone --no-checkout --filter=blob:none -c core.autocrlf=false -c core.eol=lf https://github.com/KentuckyPortableClub/KPC-Data "repos\KPC-Data-data" || (echo STOPPED: the download failed.& pause & exit /b 2)
  git -C "repos\KPC-Data-data" sparse-checkout init --cone || (echo STOPPED.& pause & exit /b 2)
  git -C "repos\KPC-Data-data" sparse-checkout set data || (echo STOPPED.& pause & exit /b 2)
)
git -C "repos\KPC-Data-data" config core.autocrlf false
git -C "repos\KPC-Data-data" config core.eol lf
rem say again that this checkout is the data folder only, so the step below can never bring the code folders down
git -C "repos\KPC-Data-data" sparse-checkout init --cone >nul 2>nul
git -C "repos\KPC-Data-data" sparse-checkout set data >nul 2>nul
git -C "repos\KPC-Data-data" fetch origin main || (echo STOPPED: could not fetch KPC-Data.& pause & exit /b 2)
rem an older folder on this PC may already hold CRLF files: forget what git thinks is on disk, then lay them down again
git -C "repos\KPC-Data-data" rm --cached -r -q . >nul 2>nul
git -C "repos\KPC-Data-data" checkout --force -B main origin/main || (echo STOPPED.& pause & exit /b 2)
rem the run plan reads ONE config file out of KPC-Data's .github folder. The checkout stays data-only, so take just that
rem one file out of the history at the pinned commit. No extra download, and no code folder lands on this PC.
if not exist "repos\KPC-Data-data\.github" mkdir "repos\KPC-Data-data\.github"
git -C "repos\KPC-Data-data" show %DC%:.github/fers-areas.json > "repos\KPC-Data-data\.github\fers-areas.json" || (echo STOPPED: could not read .github/fers-areas.json at the pinned KPC-Data commit.& pause & exit /b 2)
rem the shipped scripts in pinned\kpcdata read the same file from THEIR own folder, so put a copy there too.
if not exist "pinned\kpcdata\.github" mkdir "pinned\kpcdata\.github"
copy /y "repos\KPC-Data-data\.github\fers-areas.json" "pinned\kpcdata\.github\fers-areas.json" >nul || (echo STOPPED: could not copy fers-areas.json into pinned\kpcdata.& pause & exit /b 2)
rem Nov 16: lay the shipped KPC-Data scripts down again, straight out of the PINNED KPC-Data commit, and check every one
rem against pinned\MANIFEST.json. A pin that moves brings its code with it, and a shipped copy can never quietly fall behind.
echo.
echo --- the shipped club code
%PY% tools\kpc_pc_run.py sync-pinned || (echo STOPPED: the shipped KPC-Data code could not be laid down (see above^).& pause & exit /b 2)
rem Nov 16: the key's saved copy (public KPC-Links release, about 86 MB the first time; files already here are kept).
rem The GitHub 2-fer job downloads it before every run; without it the store run cannot read its Wild and Scenic corridors.
echo.
echo --- the key's saved copy (about 86 MB the first time)
%PY% tools\kpc_pc_run.py get-cache || (echo STOPPED: the key's saved copy could not be downloaded (see above^).& pause & exit /b 2)
echo.
echo ==========================================================
echo  Done. Now run 0-CHECK-SETUP.bat.
echo ==========================================================
pause
