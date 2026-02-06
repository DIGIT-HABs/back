# ════════════════════════════════════════════════════════
# Script de Migration des Données - SQLite vers PostgreSQL
# À exécuter sur Windows (PowerShell)
# ════════════════════════════════════════════════════════

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Migration des Données - SQLite vers PostgreSQL" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_DIR = "C:\Users\soule\Documents\projet\2025\DIGIT-HAB_CRM_\CRM\Django"
$VPS_IP = "72.60.189.237"
$VPS_USER = "root"
$VPS_PATH = "/var/www/digit-hab-crm"

# Aller dans le dossier du projet
Set-Location $PROJECT_DIR

# Activer l'environnement virtuel
Write-Host "📦 Activation de l'environnement virtuel..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Exporter les données
Write-Host ""
Write-Host "📤 Export des données depuis SQLite..." -ForegroundColor Yellow

# Applications à exporter
$apps = @(
    "auth.User",
    "auth.Agency", 
    "auth.UserProfile",
    "properties.PropertyCategory",
    "properties.Property",
    "properties.PropertyImage",
    "crm.ClientProfile",
    "crm.ClientNote",
    "crm.ClientInteraction",
    "crm.PropertyInterest",
    "crm.Lead",
    "reservations.Reservation",
    "reservations.Payment",
    "calendar",
    "reviews",
    "favorites"
)

$exportSuccess = $true

foreach ($app in $apps) {
    Write-Host "  Exportation: $app..." -ForegroundColor Gray
    try {
        python manage.py dumpdata $app --natural-foreign --natural-primary --indent 2 --output "dump_$($app.Replace('.', '_')).json"
        Write-Host "    ✅ Exporté" -ForegroundColor Green
    } catch {
        Write-Host "    ⚠️  Ignoré (pas de données ou app inexistante)" -ForegroundColor Yellow
    }
}

# Créer un dump complet
Write-Host ""
Write-Host "📦 Création du dump complet..." -ForegroundColor Yellow
python manage.py dumpdata --natural-foreign --natural-primary `
    --exclude contenttypes --exclude auth.permission --exclude sessions `
    --indent 2 --output data_full_backup.json

Write-Host "✅ Export terminé" -ForegroundColor Green

# Transférer vers le VPS
Write-Host ""
Write-Host "🚀 Transfert vers le VPS..." -ForegroundColor Yellow
scp data_full_backup.json "$VPS_USER@${VPS_IP}:$VPS_PATH/"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Fichiers transférés avec succès" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur lors du transfert" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Export et Transfert Terminés !" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Prochaines étapes sur le VPS :" -ForegroundColor Yellow
Write-Host "   1. cd /var/www/digit-hab-crm"
Write-Host "   2. docker cp data_full_backup.json digit-hab-crm-web-1:/app/"
Write-Host "   3. docker compose -f docker-compose.prod.yml exec web python manage.py loaddata /app/data_full_backup.json"
Write-Host ""
