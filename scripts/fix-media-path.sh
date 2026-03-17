#!/bin/bash
# À exécuter sur le serveur dans /var/www/digit-hab-crm
# Copie le contenu de digit_hab_crm/media/ vers media/ pour que Nginx (alias media/) les serve.
set -e
ROOT="/var/www/digit-hab-crm"
if [ ! -d "$ROOT/digit_hab_crm/media" ]; then
  echo "Dossier source $ROOT/digit_hab_crm/media introuvable."
  exit 1
fi
mkdir -p "$ROOT/media"
cp -an "$ROOT/digit_hab_crm/media/"* "$ROOT/media/" 2>/dev/null || true
echo "Contenu de digit_hab_crm/media copié vers media/."
ls -la "$ROOT/media/"
