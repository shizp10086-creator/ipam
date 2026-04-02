@echo off
chcp 65001 >nul
REM IPAM Network Diagnostic Tool (Windows)

echo =========================================
echo IPAM Network Diagnostic Tool
echo =========================================
echo.

REM Get target IP from parameter, default is 172.18.201.56
set TARGET_IP=%1
if "%TARGET_IP%"=="" set TARGET_IP=172.18.201.56
echo Target IP: %TARGET_IP%
echo.

REM 1. Show all network interfaces
echo 1. Host Network Interfaces:
echo -------------------
ipconfig | findstr /C:"IPv4"
echo.

REM 2. Show routing table
echo 2. Routing Table:
echo -------------------
route print | findstr /C:"0.0.0.0"
echo.

REM 3. Test default route ping
echo 3. Test Default Route Ping:
echo -------------------
echo Command: ping -n 1 -w 2000 %TARGET_IP%
ping -n 1 -w 2000 %TARGET_IP% >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Success: Can ping %TARGET_IP% using default route
) else (
    echo [FAIL] Failed: Cannot ping %TARGET_IP% using default route
)
echo.

REM 4. Find possible source IPs
echo 4. Find Possible Source IPs:
echo -------------------
REM Extract target network (first 3 octets)
for /f "tokens=1,2,3 delims=." %%a in ("%TARGET_IP%") do (
    set TARGET_NETWORK=%%a.%%b.%%c
)
echo Target Network: %TARGET_NETWORK%.0/24
echo.

echo Looking for IPs in this network on host:
echo.

REM Find matching network interfaces
setlocal enabledelayedexpansion
set FOUND=0
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set IP=%%a
    set IP=!IP: =!
    echo !IP! | findstr /C:"%TARGET_NETWORK%." >nul 2>&1
    if !errorlevel!==0 (
        set FOUND=1
        set SOURCE_IP=!IP!
        echo [OK] Found matching IP: !SOURCE_IP!
        echo.
        
        REM 5. Test source IP
        echo 5. Test Source IP:
        echo -------------------
        echo Testing source IP: !SOURCE_IP!
        echo Command: ping -S !SOURCE_IP! -n 1 -w 2000 %TARGET_IP%
        ping -S !SOURCE_IP! -n 1 -w 2000 %TARGET_IP% >nul 2>&1
        if !errorlevel!==0 (
            echo [OK] Success: Can ping %TARGET_IP% using source IP !SOURCE_IP!
            echo.
            echo =========================================
            echo RECOMMENDED CONFIGURATION:
            echo =========================================
            echo Add to backend\.env file:
            echo PING_SOURCE_IP=!SOURCE_IP!
            echo.
            echo Complete configuration example:
            echo USE_PING_PROXY=true
            echo PING_PROXY_URL=http://host.docker.internal:8001
            echo PING_SOURCE_IP=!SOURCE_IP!
            echo =========================================
            goto :end
        ) else (
            echo [FAIL] Failed: Cannot ping %TARGET_IP% using source IP !SOURCE_IP!
        )
        echo.
    )
)

if %FOUND%==0 (
    echo [FAIL] No matching IP address found
    echo.
    echo Suggestions:
    echo 1. Check if host is connected to target network
    echo 2. Check network configuration
    echo 3. Try manually configuring an IP in this network
)

REM 6. If all tests failed
echo.
echo =========================================
echo DIAGNOSTIC RESULT: Cannot ping target IP
echo =========================================
echo.
echo Possible reasons:
echo 1. Target device is offline or not responding to ICMP
echo 2. Firewall is blocking ICMP requests
echo 3. Network configuration error
echo 4. Host is not connected to target network
echo.
echo Suggestions:
echo 1. Check if target device is online
echo 2. Check firewall rules
echo 3. Check network connection and routing
echo 4. Try pinging target IP from another device
echo.

:end
pause
