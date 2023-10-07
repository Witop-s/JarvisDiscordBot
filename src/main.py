# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
import asyncio
import os
import feedparser
import discord
import html

import requests

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def check_films():
    while True:
        # Code à exécuter toutes les heures
        print('Executing hourly function...')

        # Récuperer la liste des films au cinéma
        # Flux RSS :
        url = "https://www.cinemagaiete.com/feed/"
        feed = feedparser.parse(url)
        films = feed.entries

        listMessage = []

        # Récuperer le channel
        channel = client.get_channel(1159950676521123890)

        for film in films:
            message = ""

            # Si le titre en minuscule contient "offre", publicité" ou "promo" on passe au film suivant
            if "offre" in film.title.lower() or "publicité" in film.title.lower() or "promo" in film.title.lower():
                break

            link = film.link
            description = html.unescape(film.description)

            # Si le description est vide, on passe au film suivant
            if description == "":
                continue

            message += "**" + film.title + "**"
            message += "\n" + "*" + description + "*"
            message += "\n" + "||" + link + "||"
            listMessage.append(message)

        for message in listMessage:
            # Si ce n'est pas le dernier message, on ajoute une ligne de séparation
            if message != listMessage[-1]:
                message += "\n\n" + html.unescape("\u200B")
            await channel.send(message)

        await asyncio.sleep(3600)  # Attendre 1 heure (3600 secondes)

@client.event
async def test_fb():
    print("test fb")
    app_id = '701046464836944'  # Remplacez par votre app_id
    secret = '16c27e2c4ec50b8f008aa2e285dd6e9d'  # Remplacez par votre secret

    page_name = 'cinemagaiete'  # Nom de la page Facebook que vous souhaitez récupérer. Ce nom est celui dans l'URL de la page et non le nom réel. Ex: https://www.facebook.com/LemonCake/

    fb_token = app_id + '|' + secret  # On prépare le token en séparant app_id et secret par un |

    # Via cette URL on va récupérer l'identifiant unique de la page pour récupérer les données
    page_url = 'https://graph.facebook.com/' + page_name + '?fields=fan_count,talking_about_count,name&access_token=' + fb_token
    page_response = requests.get(page_url)
    page_data = page_response.json()

    # Récupération de l'identifiant unique de la page
    print(page_data)
    page_id = page_data['id']

    # Récupération du flux de la page
    # Dans cette URL on peut voir que je demande de récupérer :
    # - L'image du poste
    # - Le message
    # - La date de création
    # - Les partages
    # - Les likes et commentaires dont vous pouvez modifier la limite qui là est de 1
    feed_url = f"https://graph.facebook.com/v18.0/{page_id}/feed?fields=picture,message,story,created_time,shares,likes.limit(1).summary(true),comments.limit(1).summary(true)&access_token={fb_token}"
    feed_response = requests.get(feed_url)
    feed_data = feed_response.json()
    print(feed_data)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # client.loop.create_task(checkFilms())
    await test_fb()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e
