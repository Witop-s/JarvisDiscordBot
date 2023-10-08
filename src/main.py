# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
import asyncio
import os
from urllib.request import Request

import feedparser
import discord
import html

import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def get_html(url):
    # Envoyez une requête HTTP GET pour obtenir le contenu de la page
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(response.status_code)
    return response.text

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

            contenu = await get_html(link)
            soup = BeautifulSoup(contenu, 'html.parser')
            #print(soup.prettify())

            # Trouver l'élément img
            # Utiliser un sélecteur CSS plus précis pour cibler l'élément img
            img_element = soup.select_one('.attachment-cine-thumbthumb.wp-post-image')
            image_url = img_element['src']
            print(image_url)

            print("image_url : " + image_url)

            titre = "**" + film.title.upper() + "**"
            listMessage.append(titre)
            image = "\n" + image_url
            listMessage.append(image)
            message += "\n" + "*" + description + "*"
            #message += "\n" + "||" + "[+](" + link + ")" + "||"
            listMessage.append(message)

        for message in listMessage:
            # Tous les 3 messages, et si le message n'est pas le dernier, on ajoute un saut de ligne
            if (listMessage.index(message)+1) % 3 == 0 and listMessage.index(message) != len(listMessage) - 1:
                message += "\n" + html.unescape("\u200B")
                print("modif" + message)
            await channel.send(message)

        await asyncio.sleep(3600)  # Attendre 1 heure (3600 secondes)"""

        # TODO : Ajouter un système de cache pour ne pas envoyer les mêmes films plusieurs fois
        # TODO : Prendre la description via le web scraping
        # TODO : Ajouter la mention @cinephile
        # TODO : Ajouter les horaires
        # TODO : Enlever ce break
        break


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # client.loop.create_task(checkFilms())
    await check_films()


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
