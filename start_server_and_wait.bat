@echo off
echo ========================================
echo Demarrage du serveur Django
echo ========================================
cd /d C:\Users\soule\Documents\projet\2025\DIGIT-HAB_CRM_\CRM\Django
start /B python manage.py runserver > server.log 2>&1
echo Attente du demarrage du serveur...
timeout /t 10 /nobreak
echo.
echo Serveur demarre !
echo Consultez server.log pour les details

