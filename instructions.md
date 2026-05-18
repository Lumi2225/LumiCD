# CD Web Player - Installation sur Debian

Ce guide vous explique comment installer et lancer le lecteur CD Web "CD Web Player" sur un système Debian (ou Ubuntu).

## 1. Dépendances Système

Le projet nécessite FFmpeg pour le streaming, `libdiscid` pour l'identification des CD, et les outils `libcdio` pour la lecture directe.

Ouvrez un terminal et installez les paquets nécessaires :

```bash
sudo apt update
sudo apt install -y ffmpeg libdiscid-dev libcdio-utils python3-pip eject
```

### Note sur FFmpeg
Assurez-vous que votre version de FFmpeg supporte `libcdio`. Vous pouvez vérifier avec :
```bash
ffmpeg -demuxers | grep libcdio
```
Si vous voyez `D  libcdio         libcdio CDDA input`, c'est parfait.

## 2. Permissions du Lecteur CD

Le serveur doit avoir les droits de lecture sur `/dev/sr0`. Vous pouvez ajouter votre utilisateur au groupe `cdrom` :

```bash
sudo usermod -aG cdrom $USER
```
*Note : Déconnectez-vous et reconnectez-vous pour que le changement de groupe soit effectif.*

## 3. Installation des Dépendances Python

Il est recommandé d'utiliser un environnement virtuel :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Lancer l'Application

```bash
python3 app.py
```

L'application sera accessible sur `http://localhost:5000` (ou l'IP de votre serveur).

## Fonctionnement
- **Mode Réel** : Insérez un CD audio. L'application détectera automatiquement le disque, récupérera les pochettes et titres via MusicBrainz, et permettra le streaming.
- **Streaming iPhone/Safari** : L'application bascule automatiquement sur un flux MP3 pour la compatibilité avec iOS.
- **Contrôles** : Play/Pause, Suivant, Précédent, Éjection.
