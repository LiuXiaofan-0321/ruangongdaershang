@echo off
chcp 65001 >nul
echo === Interface (WLAN) ===
powershell -NoProfile -Command "Get-NetIPConfiguration -InterfaceAlias WLAN | Format-List InterfaceAlias, InterfaceDescription, IPv4Address, IPv4DefaultGateway, @{n='MAC'; e={$_.NetAdapter.MacAddress}}"
