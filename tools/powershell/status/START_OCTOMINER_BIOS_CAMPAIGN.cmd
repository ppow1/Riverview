@echo off
set "RIVERVIEW=A:\Riverview\standalone"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%RIVERVIEW%\tools\powershell\status\Start-OctoMinerBIOSCampaign.ps1"
