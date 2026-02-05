#!/bin/bash
# Script pour nettoyer et réinstaller Docker proprement

echo "🧹 Nettoyage de la configuration Docker existante..."

# Supprimer les anciennes clés GPG
sudo rm -f /etc/apt/keyrings/docker.gpg
sudo rm -f /etc/apt/keyrings/docker.asc
sudo rm -f /usr/share/keyrings/docker-archive-keyring.gpg

# Supprimer les anciennes sources
sudo rm -f /etc/apt/sources.list.d/docker.list

# Supprimer les anciennes installations Docker
sudo apt-get remove -y docker docker-engine docker.io containerd runc docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null

# Nettoyer les paquets
sudo apt-get autoremove -y
sudo apt-get autoclean

echo "✅ Nettoyage terminé"
echo ""
echo "📦 Installation des prérequis..."

# Mettre à jour les paquets
sudo apt-get update

# Installer les prérequis
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

echo "🔑 Ajout de la clé GPG Docker..."

# Créer le dossier keyrings s'il n'existe pas
sudo mkdir -p /etc/apt/keyrings

# Ajouter la clé GPG officielle de Docker (nouvelle méthode)
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "📝 Ajout du dépôt Docker..."

# Ajouter le dépôt Docker aux sources APT
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "🔄 Mise à jour des paquets..."

# Mettre à jour la liste des paquets
sudo apt-get update

echo "🐳 Installation de Docker..."

# Installer Docker Engine
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

echo "✅ Docker installé avec succès !"
echo ""
echo "🔧 Configuration post-installation..."

# Démarrer et activer Docker
sudo systemctl start docker
sudo systemctl enable docker

# Ajouter l'utilisateur courant au groupe docker
sudo usermod -aG docker $USER

echo "✅ Configuration terminée !"
echo ""
echo "📊 Vérification de l'installation..."

# Vérifier les versions
docker --version
docker compose version

echo ""
echo "🎉 Installation complète !"
echo ""
echo "⚠️  IMPORTANT : Vous devez vous déconnecter et vous reconnecter pour que"
echo "    les changements de groupe prennent effet, ou exécutez :"
echo "    newgrp docker"
echo ""
echo "🧪 Pour tester Docker, exécutez :"
echo "    docker run hello-world"
