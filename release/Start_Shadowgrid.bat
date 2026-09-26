@echo off
cd /d "%~dp0"
if exist "ShadowgridLauncher.exe" (
    start "" "ShadowgridLauncher.exe"
) else (
    start "" "Shadowgrid\Shadowgrid.exe"
)
