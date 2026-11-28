@echo off
chcp 65001 >nul
echo $ nslookup www.baidu.com
nslookup www.baidu.com
echo.
echo $ w32tm /stripchart /computer:ntp.aliyun.com /samples:2 /dataonly
w32tm /stripchart /computer:ntp.aliyun.com /samples:2 /dataonly
