# MataneDiscordCGBot

Libs :
- pip-24.0
- APScheduler 3.10.0
- py-cord 2.5
- beautifulsoup4 4.13.0b2
- requests 2.31.0
- selenium 4.19.0
- feedparser 6.0.11

## Installation 
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

# Cloner le dépôt GitHub
git clone https://github.com/Witop-s/JarvisDiscordBot.git /home/username/JarvisDiscordBot/bot  

# Installer les packets requis
python3 -m pip install requirements.txt

# Exporter le répertoire source
export PYTHONPATH=/home/username/JarvisDiscordBot/bot/src:$PYTHONPATH

nano /home/username/JarvisDiscordBot/bot/src/.env
  OPENAI=[clé open ai];
  PYTHONBUFFERED=1;
  SYSTEM_PROMPT=[prompt système pour jarvis];

# Note : si vous avez une erreur par rapport à l'import de bot_commands et minecraft, il faudra peut-être rajouter "from src import" au lieu de juste "import ..."
# Idéalement ce problème devrait être réglé dans le futur

# Host le bot
screen -S JarvisSession
python /home/username/JarvisDiscordBot/bot/src/main.py

# Détacher la session
ctrl-a d

# Désactiver l'environnement
deactivate

# Se reconecter à la session
screen -r JarvisSession

```

## Avec docker (généralement plus pratique pour le serveur, moins pratique pour le dev)

``` 
nano /home/username/JarvisDiscordBot/bot/src/.env      # Noter la différence de placement du .env

docker compose build
docker compose up
```   
