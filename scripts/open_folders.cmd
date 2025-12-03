@echo off
setlocal
cd /d %~dp0..
start "" explorer ".\data\raw"
start "" explorer ".\data\index"
endlocal
