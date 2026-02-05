#!/bin/bash
# ════════════════════════════════════════════════════════
# Diagnostic Rapide - Problème Certbot
# ════════════════════════════════════════════════════════

echo "🔍 Diagnostic du problème Certbot..."
echo ""

# 1. Vérifier le dossier sur l'hôte
echo "1️⃣  Dossier /var/www/certbot sur l'hôte:"
ls -la /var/www/certbot/ 2>/dev/null || echo "   ❌ Dossier n'existe pas"
echo ""

# 2. Créer un fichier de test
echo "2️⃣  Création d'un fichier de test:"
mkdir -p /var/www/certbot/.well-known/acme-challenge/
echo "TEST OK" > /var/www/certbot/.well-known/acme-challenge/test.txt
chmod -R 755 /var/www/certbot
echo "   ✅ Fichier test créé: /var/www/certbot/.well-known/acme-challenge/test.txt"
echo ""

# 3. Vérifier le docker-compose d'AL-TOPPE
echo "3️⃣  Volumes montés dans docker-compose.prod.yml d'AL-TOPPE:"
cd /var/www/al-toppe
grep -A 10 "nginx:" docker-compose.prod.yml | grep -E "volumes:|certbot" || echo "   ⚠️  Volume certbot non trouvé"
echo ""

# 4. Vérifier si le dossier est accessible depuis le conteneur
echo "4️⃣  Test d'accès depuis le conteneur Nginx:"
docker compose -f docker-compose.prod.yml exec nginx ls -la /var/www/certbot/.well-known/acme-challenge/ 2>/dev/null || echo "   ❌ Dossier non accessible depuis le conteneur"
echo ""

# 5. Vérifier la config Nginx
echo "5️⃣  Configuration Nginx (server block port 80):"
docker compose -f docker-compose.prod.yml exec nginx cat /etc/nginx/nginx.conf 2>/dev/null | grep -A 8 "listen 80" | head -12
echo ""

# 6. Test HTTP depuis l'extérieur
echo "6️⃣  Test HTTP depuis l'extérieur:"
echo "   URL: http://digit-hab.altoppe.sn/.well-known/acme-challenge/test.txt"
curl -v http://digit-hab.altoppe.sn/.well-known/acme-challenge/test.txt 2>&1 | grep -E "HTTP|< Location|TEST OK" | head -5
echo ""

# 7. Résumé
echo "════════════════════════════════════════════════════════"
echo "📋 Résumé du Diagnostic"
echo "════════════════════════════════════════════════════════"
echo ""
echo "✅ = OK    ⚠️  = Attention    ❌ = Problème"
echo ""
echo "Actions recommandées :"
echo "  1. Si le volume certbot n'est pas monté dans docker-compose :"
echo "     → Modifier docker-compose.prod.yml d'AL-TOPPE"
echo ""
echo "  2. Si le dossier n'est pas accessible depuis le conteneur :"
echo "     → Redémarrer Nginx après avoir ajouté le volume"
echo ""
echo "  3. Si le test HTTP retourne 404 ou 301 :"
echo "     → Vérifier la config Nginx (nginx.prod.conf)"
echo ""
