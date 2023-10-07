# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
import asyncio
import os
import feedparser
import discord
import html

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def checkFilms():
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
            print(film.title)
            # Si le titre en minuscule contient "offre", publicité" ou "promo" on passe au film suivant
            if "offre" in film.title.lower() or "publicité" in film.title.lower() or "promo" in film.title.lower():
                break

            link = film.link
            print(link)

            description = html.unescape(film.description)
            print(description)

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
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    client.loop.create_task(checkFilms())


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
