@echo off
setlocal

set "PLUGIN_DIR=%~dp0"
set "NODE=C:\Program Files\nodejs\node.exe"

if not exist "%NODE%" (
    for /f "delims=" %%I in ('where.exe node 2^>nul') do (
        set "NODE=%%~fI"
        goto node_resolved
    )
)

:node_resolved
if not exist "%NODE%" (
    echo RIV-SD-0003: node.exe not found >> "%PLUGIN_DIR%riverview-native-plugin.log"
    exit /b 2
)

echo START %* >> "%PLUGIN_DIR%riverview-native-plugin.log"
"%NODE%" "%PLUGIN_DIR%plugin.js" %* >> "%PLUGIN_DIR%riverview-native-plugin.log" 2>&1
set "RC=%ERRORLEVEL%"
echo EXIT %RC% >> "%PLUGIN_DIR%riverview-native-plugin.log"
exit /b %RC%
