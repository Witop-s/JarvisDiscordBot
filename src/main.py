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
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

id_salon_film = 1159950676521123890
role_cinephile = 1160395562022084652


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
        channel = client.get_channel(id_salon_film)

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
            # message += "\n" + "*" + description + "*"
            # message += "\n" + "||" + "[+](" + link + ")" + "||"
            # listMessage.append(message)

            # Trouver l'élément avec la date "Dès le"
            date_element = soup.select_one('p:-soup-contains("Dès le")')
            date = date_element.text.strip()
            date = date.title()
            date = date.replace("Le", "le")
            print("date" + date)

            representations = "**" + date + "**" + "\n"
            print("représentations date : " + representations)
            if not "A Venir" in date:
                # Trouver l'élément avec le genre
                genre_element = soup.select_one('p:-soup-contains("Genre :")')
                genre = genre_element.text.strip()
                print(genre)

                # Trouver l'élément avec la durée
                duree_element = soup.select_one('p:-soup-contains("Durée :")')
                duree = duree_element.text.strip()
                print(duree)

                # Trouver l'élément avec les représentations
                representations_element = soup.select_one('strong:-soup-contains("Représentation :")')
                # Tant que l'élément suivant contient un jour de la semaine, on ajoute le texte à la variable representations

                jours_semaine = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
                representations_element = representations_element.find_next_sibling("p")

                while any(jour in representations_element.text.strip() for jour in jours_semaine):
                    # Prendre seulement la première ligne
                    jours = representations_element.text.strip().split("\n")[0]
                    heures = representations_element.text.strip().split("\n")[1]
                    representations += jours.title() + " - " + heures + "\n"

                    representations_element = representations_element.find_next_sibling("p")

                print(representations)

            synopsis_element = soup.select_one('strong:-soup-contains("Synopsis :")')
            synopsis = synopsis_element.find_next_sibling("p").text.strip()
            print(synopsis)
            representations += "\n" + "*" + synopsis + "*"
            listMessage.append(representations)

        for message in listMessage:
            # Tous les 3 messages, et si le message n'est pas le dernier, on ajoute un saut de ligne et une réaction
            is_end_film = (listMessage.index(message) + 1) % 3 == 0
            if is_end_film and listMessage.index(message) != len(listMessage) - 1:
                #message += "\n" + html.unescape("\u200B")
                print()
            sent_message = await channel.send(message)
            if is_end_film:
                await sent_message.add_reaction("✋")

        role = discord.utils.get(channel.guild.roles, id=role_cinephile)
        last_message = f"{role.mention} \nDe nouveaux films sont disponibles !"
        last_message += "\n\n" + ":popcorn: Tu va voir un film ? Fait le savoir ✋ !"
        last_message += "\n\n" + "*Tu veux être notifié des nouveaux films ? Abonne toi ! :bell:*"
        last_sent_message = await channel.send(last_message)
        await last_sent_message.add_reaction("🔔")

        await asyncio.sleep(3600)  # Attendre 1 heure (3600 secondes)"""

        # TODO : Ajouter un système de cache pour ne pas envoyer les mêmes films plusieurs fois
        # TODO : Enlever ce break
        break

@client.event
async def on_raw_reaction_add(payload):
    print("on_raw_reaction_add")
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.channel_id == id_salon_film:
        # Votre code ici
        if payload.member.bot:
            return  # Ignorer les réactions du bot
        if payload.emoji.name == "🔔":
            user = payload.member
            role = discord.utils.get(user.guild.roles, id=role_cinephile)
            await user.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    print("on_raw_reaction_remove")
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.channel_id == id_salon_film and payload.emoji.name == "🔔":
        guild = client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        role = discord.utils.get(user.guild.roles, id=role_cinephile)
        await user.remove_roles(role)


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
