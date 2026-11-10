@echo off
chcp 65001 >nul
echo === Default route 0.0.0.0/0  (netstat -r equivalent) ===
echo.
powershell -NoProfile -Command "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Format-Table ifIndex, InterfaceAlias, NextHop, RouteMetric -AutoSize"
echo === On-link IPv4 routes on WLAN ===
echo.
powershell -NoProfile -Command "Get-NetRoute -InterfaceAlias WLAN -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -notlike 'ff00*' } | Select-Object -First 6 DestinationPrefix, NextHop, RouteMetric | Format-Table -AutoSize"
