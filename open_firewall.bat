@echo off
title Mo Cong Windows Firewall Cho FlappyBirdServer (Port 8889)
echo ==================================================================
echo   MO CONG WINDOWS DEFENDER FIREWALL CHO FLAPPY BIRD SERVER (8889)
echo ==================================================================
echo.
echo Dang kiem tra quyen Administrator...
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [CANH BAO] Ban chua chay voi quyen Administrator!
    echo Vui long chuot phai vao file open_firewall.bat va chon "Run as administrator".
    echo.
    pause
    exit /b
)

echo Dang them rule cho phep ket noi Inbound TCP cong 8889...
netsh advfirewall firewall delete rule name="FlappyBirdServer_TCP8889" >nul 2>&1
netsh advfirewall firewall add rule name="FlappyBirdServer_TCP8889" dir=in action=allow protocol=TCP localport=8889 profile=any

echo.
echo ==================================================================
echo [OK] DA MO THANH CONG CONG 8889 TREN WINDOWS FIREWALL!
echo Gio day dien thoai Android cung mang Wi-Fi co the ket noi toi IP:
ipconfig | findstr "IPv4"
echo ==================================================================
echo.
pause
