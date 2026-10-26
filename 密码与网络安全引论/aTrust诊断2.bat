@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"
set "RAW=%~dp0diag2_raw.txt"
set "OUT=%~dp0diag2_report.txt"

> "%RAW%" echo ==================================================
>>"%RAW%" echo   Diagnostics v2  -  post-reboot
>>"%RAW%" echo   Time: %date% %time%
>>"%RAW%" echo ==================================================

net session >nul 2>&1
if errorlevel 1 >>"%RAW%" echo [WARN] Not elevated - some sections incomplete.

>>"%RAW%" echo.
>>"%RAW%" echo ===== A. GATEWAY REACHABILITY =====
ping -n 2 192.168.31.1 >>"%RAW%" 2>&1
>>"%RAW%" echo ----- ARP -----
arp -a >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== B. OUTBOUND HTTPS TESTS =====
>>"%RAW%" echo --- baidu.com ---
curl -s -o nul -w "http_code=%%{http_code} connect=%%{time_connect} total=%%{time_total}\n" --max-time 8 https://www.baidu.com >>"%RAW%" 2>&1
>>"%RAW%" echo --- 223.5.5.5 dns over https ---
curl -s -o nul -w "http_code=%%{http_code} total=%%{time_total}\n" --max-time 8 https://223.5.5.5 >>"%RAW%" 2>&1
>>"%RAW%" echo --- proxy server 64.186.227.37:443 tcp ---
powershell -NoProfile -Command "$r=Test-NetConnection -ComputerName 64.186.227.37 -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue; Write-Output ('tcp443_reachable=' + $r)" >>"%RAW%" 2>&1
>>"%RAW%" echo --- dns resolve test ---
nslookup www.baidu.com >>"%RAW%" 2>&1
nslookup www.google.com >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== C. ADAPTERS =====
ipconfig /all >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== D. ROUTES IPv4 =====
route print -4 >>"%RAW%" 2>&1
>>"%RAW%" echo.
>>"%RAW%" echo ===== D2. ROUTES IPv6 =====
route print -6 >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== E. ADAPTER BINDINGS =====
powershell -NoProfile -Command "Get-NetAdapter | Format-Table Name,InterfaceDescription,Status,LinkSpeed -AutoSize | Out-String -Width 200" >>"%RAW%" 2>&1
>>"%RAW%" echo ----- bindings on wired NIC -----
powershell -NoProfile -Command "Get-NetAdapterBinding -Name '*' | Where-Object {$_.Enabled -eq $true} | Format-Table Name,ComponentID,DisplayName -AutoSize | Out-String -Width 200" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== F. SANGFOR DRIVER / SERVICE STATE =====
sc qc aTrustNetflt_1 >>"%RAW%" 2>&1
sc query aTrustNetflt_1 >>"%RAW%" 2>&1
sc query aTrustService >>"%RAW%" 2>&1
sc query aTrustXtun >>"%RAW%" 2>&1
>>"%RAW%" echo ----- fltmc filters -----
fltmc filters >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== G. PROCESSES =====
tasklist | findstr /i "atrust sangfor v2ray xray sing-box wintun" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== H. PROXY SETTINGS =====
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer >>"%RAW%" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoConfigURL >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== I. FIREWALL =====
netsh advfirewall show allprofiles state >>"%RAW%" 2>&1
>>"%RAW%" echo ----- blocking rules mentioning sangfor/atrust -----
powershell -NoProfile -Command "Get-NetFirewallRule -Enabled True -Action Block | Select-Object -First 40 DisplayName,Direction,Action | Format-Table -AutoSize | Out-String -Width 200" >>"%RAW%" 2>&1

>>"%RAW%" echo.
>>"%RAW%" echo ===== END =====

powershell -NoProfile -Command "Get-Content -LiteralPath '%RAW%' | Set-Content -LiteralPath '%OUT%' -Encoding UTF8"

cls
type "%RAW%"
echo.
echo ============================================================
echo  Report: %OUT%
echo ============================================================
pause
