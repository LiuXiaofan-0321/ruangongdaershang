@echo off
chcp 65001 >nul
echo === Wireless LAN adapter WLAN  (ipconfig /all) ===
echo.
powershell -NoProfile -Command "Get-NetIPConfiguration -InterfaceAlias WLAN | Format-List InterfaceAlias, InterfaceDescription, @{n='PhysicalAddress(MAC)';e={$_.NetAdapter.MacAddress}}, @{n='IPv4Address';e={$_.IPv4Address.IPAddress}}, @{n='PrefixLength';e={$_.IPv4Address.PrefixLength}}, @{n='DefaultGateway';e={$_.IPv4DefaultGateway.NextHop}}, @{n='DHCP';e={$_.NetIPv4Interface.Dhcp}}"
