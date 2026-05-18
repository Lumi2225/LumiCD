# CD Web Player - Instructions d'installation

Ce projet permet de transformer un serveur Debian (ou autre Linux) avec un lecteur CD en un lecteur de musique connecté moderne.

## 1. Prérequis Système

Vous devez installer les outils système nécessaires pour la lecture de CD et le traitement audio.

```bash
sudo apt update
sudo apt install -y ffmpeg libdiscid0 eject python3-pip
```

## 2. Installation de l'application

1. Clonez ou copiez les fichiers du projet.
2. Installez les dépendances Python :

```bash
pip install -r requirements.txt
```

Note : Si vous utilisez un environnement virtuel (recommandé) :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration des permissions

Le serveur Flask doit avoir les droits de lecture sur le périphérique CD (`/dev/sr0`).
Ajoutez l'utilisateur courant au groupe `cdrom` :

```bash
sudo usermod -a -G cdrom $USER
```
*Déconnectez-vous et reconnectez-vous pour que le changement soit pris en compte.*

## 4. Lancer le serveur

```bash
python3 app.py
```

Le site sera accessible à l'adresse : `http://votre-ip:5000`

## 5. Fonctionnement

- Insérez un CD Audio dans le lecteur.
- L'interface se mettra à jour automatiquement avec les métadonnées (Artiste, Album, Titres) récupérées sur MusicBrainz.
- Utilisez les contrôles pour naviguer entre les pistes.
- Le flux audio est encodé en temps réel en OGG pour une compatibilité maximale et une faible latence.

## Structure du projet

- `app.py` : Serveur Flask & API REST / Streaming.
- `templates/` : Page HTML principale.
- `static/` : Styles CSS (Tailwind) et Logique JavaScript.
- `requirements.txt` : Dépendances Python.
