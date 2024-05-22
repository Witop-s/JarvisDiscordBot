# MataneDiscordCGBot

Libs :
- pip-24.0
- APScheduler 3.10.0
- py-cord 2.5
- beautifulsoup4 4.13.0b2
- opencv-python 4.9.0.80
- requests 2.31.0
- pdf2image 1.17.0
- selenium 4.19.0
- feedparser 6.0.11

# Installation 
```bash
#!/bin/bash

# Créer un répertoire pour le projet
mkdir -p /home/username/JarvisDiscordBot

# Créer un environnement virtuel Python
python3 -m venv /home/username/JarvisDiscordBot/jarvenv

# Activer l'environnement virtuel
source /home/username/JarvisDiscordBot/jarvenv/bin/activate

# Mettre à jour pip
python3 -m pip install --upgrade pip==24.0

# Installer les paquets requis
python3 -m pip install APScheduler==3.10.0
python3 -m pip install py-cord==2.5
python3 -m pip install beautifulsoup4==4.13.0b2
python3 -m pip install opencv-python==4.9.0.80
python3 -m pip install requests==2.31.0
python3 -m pip install pdf2image==1.17.0
python3 -m pip install selenium==4.19.0
python3 -m pip install feedparser==6.0.11
python3 -m pip install python-dotenv


# Cloner le dépôt GitHub
git clone https://github.com/Witop-s/JarvisDiscordBot.git /home/username/JarvisDiscordBot/bot

# Exporter le répertoire source
export PYTHONPATH=/home/username/JarvisDiscordBot/bot/src:$PYTHONPATH

nano /home/username/JarvisDiscordBot/bot/src/.env
  OPENAI=[clé open ai];
  PYTHONBUFFERED=1;
  SYSTEM_PROMPT=[prompt système pour jarvis];

# Host le bot
screen -S JarvisSession
python /home/username/JarvisDiscordBot/bot/src/main.py

# Détacher la session
ctrl-a d

# Se reconecter à la session
screen -r JarvisSession

```
