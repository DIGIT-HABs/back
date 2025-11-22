@echo off
echo ====================================
echo Arret du serveur Django...
echo ====================================
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo ====================================
echo Test du serializer...
echo ====================================
python quick_test.py

echo.
echo ====================================
echo Redemarrage du serveur...
echo ====================================
start /B python manage.py runserver

echo.
echo ====================================
echo Serveur demarre!
echo Testez: http://localhost:8000/api/docs/
echo ====================================

