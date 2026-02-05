@echo off
echo ============================================
echo    REDEMARRAGE DJANGO DIGIT-HAB CRM
echo ============================================
echo.

echo [1/2] Arret du serveur en cours...
echo      Appuyez sur Ctrl+C si un serveur tourne
echo.

echo [2/2] Demarrage du serveur...
python manage.py runserver 0.0.0.0:8000

echo.
echo ============================================
echo    Serveur Django demarre !
echo    URL: http://192.168.1.82:8000
echo ============================================
pause
