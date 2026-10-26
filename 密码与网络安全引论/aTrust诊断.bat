@echo off
setlocal
cd /d "%~dp0"
set "RAW=%~dp0diag_raw.txt"
set "OUT=%~dp0diag_report.txt"

> "%RAW%" echo ==================================================
>>"%RAW%" echo   aTrust / v2rayN Network Diagnostics
>>"%RAW%" echo   Time: %date% %time%
>>"%RAW%" echo   Host: %COMPUTERNAME%   User: %USERNAME%
>>"%RAW%" echo ==================================================

net session >nul 2>&1
if errorlevel 1 >>"%RAW%" echo [WARN] Not elevated - some sections may be incomplete.

>>"%RAW%" echo.
>>"%RAW%" echo ===== 1. SYSTEM PROXY - WinINET registry =====
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoConfigURL >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Connections" >>"%RAW%" 2>&1
>>"%RAW%" echo.
>>"%RAW%" echo ----- netsh winhttp proxy -----
netsh winhttp show proxy >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 2. ADAPTERS / IP / DNS =====
ipconfig /all >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 3. ROUTING TABLE - IPv4 =====
route print -4 >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 4. RELEVANT PROCESSES =====
tasklist | findstr /i "atrust sangfor v2ray xray sing-box wintun" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 5. SERVICES / DRIVERS =====
sc query type= service state= all | findstr /i "sangfor atrust sslvpn" >>"%RAW%" 2>&1
sc query type= driver state= all | findstr /i "sangfor atrust sslvpn wintun" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 6. TCP LISTENING PORTS =====
netstat -ano -p tcp | findstr LISTENING | findstr /i "10808 10809 2080 7890 8888 127.0.0.1" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 7. HOSTS FILE =====
type "%SystemRoot%\System32\drivers\etc\hosts" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 8. FIREWALL PROFILES =====
netsh advfirewall show allprofiles state >>"%RAW%" 2>&1
>>"%RAW%" echo ----- portproxy -----
netsh interface portproxy show all >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== 9. WINSOCK LSP CATALOG =====
netsh winsock show catalog >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== END =====

powershell -NoProfile -Command "Get-Content -LiteralPath '%RAW%' | Set-Content -LiteralPath '%OUT%' -Encoding UTF8"

cls
type "%RAW%"
echo.
echo ============================================================
echo  Done. Report saved to:
echo  %OUT%
echo ============================================================
pause
