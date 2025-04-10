import datetime
import glob
import json
import os

import feedparser
import html
from bs4 import BeautifulSoup

import discord
import time
import pytz

import requests

from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By

client = None
salons = None
roles = None
achievements = None
misc = None
scheduler = None
openai_token = None

prompt_test = ""


async def importer(vClient, vSalons, vRoles, vAchievements, vMisc, vScheduler, vOpenai_token):
    print("commands importer")
    global client, salons, roles, achievements, misc, scheduler, openai_token
    client = vClient
    salons = vSalons
    roles = vRoles
    achievements = vAchievements
    misc = vMisc
    scheduler = vScheduler
    openai_token = vOpenai_token


async def commands_manager(message):
    #print("commands_manager : " + message.content)
    print("commands_manager")
    if message.content.startswith("/kill") and message.author.guild_permissions.administrator:
        exit(0)

    # Si le message est check_films et que l'auteur est un admin
    elif message.content == "/check_films" and message.author.guild_permissions.administrator:
        await check_films()

    elif message.content.startswith("/prompt"):
        # Récuperer le prompt
        prompt = message.content.split("/prompt ")[1]
        global prompt_test
        prompt_test = prompt

    # Si le message est /ping je réponds pong
    elif message.content == "/ping":
        await message.channel.send("pong " + str(round(client.latency, 2)) + "ms")

    # Si le message commence par /send et que l'auteur est un admin
    elif message.content.startswith("/send") and message.author.guild_permissions.administrator:
        # Récuperer le message à envoyer
        message_to_send = message.content.split("/send ")[1]
        # Récuperer le dernier channel mentionné dans le message
        channel = message.channel_mentions[len(message.channel_mentions) - 1]
        # Supprimer seulement la dernière mention
        message_to_send = message_to_send.replace(channel.mention, "")
        # Envoyer le message
        await channel.send(message_to_send)

    elif message.content.startswith("/edit") and message.author.guild_permissions.administrator:
        # Récuperer le message à envoyer
        message_to_send = message.content.split("/edit ")[1]
        # Récuperer le dernier channel mentionné dans le message
        channel = message.channel_mentions[len(message.channel_mentions) - 1]
        # Supprimer seulement la dernière mention
        message_to_send = message_to_send.replace(channel.mention, "")
        # Récuperer le message a éditer
        message_id = message_to_send.split("\n")[0]
        # Récuperer le message
        message_to_edit = await channel.fetch_message(message_id)
        # Supprimer l'id du message
        message_to_send = message_to_send.replace(message_id, "")
        # Editer le message
        await message_to_edit.edit(content=message_to_send)

    elif message.content.startswith("/reaction") and message.author.guild_permissions.administrator:
        # Récuperer le channel du message a réagir
        channel = message.channel_mentions[len(message.channel_mentions) - 1]
        # Récuperer le message a réagir
        message = message.content.split("/reaction ")[1]
        # Prendre seulement l'id du message (en première position)
        message_id = message.split(" ")[0]
        # Récuperer le message
        message_to_react = await channel.fetch_message(message_id)
        # Récuperer la ou les réactions qui se situe après la mention du channel
        reactions = []
        # Split pour chaque character
        for reaction in message.split(channel.mention)[1].split(","):
            reactions.append(reaction.strip())
        for reaction in reactions:
            # Ajouter la réaction
            print(reaction)
            await message_to_react.add_reaction(reaction)

    elif message.content.startswith("/unreaction") and message.author.guild_permissions.administrator:
        # Récuperer le channel du message a dé-réagir
        channel = message.channel_mentions[len(message.channel_mentions) - 1]
        # Récuperer le message a réagir
        message = message.content.split("/unreaction ")[1]
        # Prendre seulement l'id du message (en première position)
        message_id = message.split(" ")[0]
        # Récuperer le message
        message_to_unreact = await channel.fetch_message(message_id)
        # Enlever toutes les réactions
        await message_to_unreact.clear_reactions()

    elif "jarvis" in message.content.lower() and (
            message.channel == client.get_channel(salons['id_salon_jarvis'])
            or message.channel == client.get_channel(salons['id_salon_bots'])
            or message.channel == client.get_channel(salons['id_salon_prive_W'])
            or message.channel == client.get_channel(salons['id_salon_jarvis_testeur'])):
        # bot is typing effect
        print("jarvis : " + message.content.lower())
        async with message.channel.typing():
            await trigger_jarvis(message)

async def messages_formater(messages, system_prompt=None):
    # inverser l'ordre des messages
    print(system_prompt)
    messages.reverse()
    messages_formated = []
    # [{"role": "user", "content": prompt}]
    if system_prompt is None:
        system_prompt = os.getenv("SYSTEM_PROMPT") or ""
        if system_prompt == "":
            raise Exception("SYSTEM_PROMPT is empty")

    messages_formated.append({"role": "system", "content": system_prompt})
    for message in messages:
        # Séparer le nom du message
        utilisateur = message.split(" : ", maxsplit=2)[1]
        if utilisateur.lower() == "cegep-bot":
            message = message.split(" : ", maxsplit=2)[2]
            messages_formated.append({"role": "assistant", "content": message})
        elif utilisateur.lower() == "system":
            message = message.split(" : ", maxsplit=2)[2]
            messages_formated.append({"role": "system", "content": message})
        else:
            messages_formated.append({"role": "user", "content": message})

    return messages_formated


async def get_completion(messages, temperature=0.8, origine=None):
    print("get_completion, messages : ")
    print(messages)

    model = "gpt-3.5-turbo"

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_token}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000,
    }

    # Effectuer une requête POST avec la bibliothèque requests
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # chercher le message via ["choices"][0]["message"]["content"]
    print(response.json())
    print(response.status_code)
    try:
        reponse_content = response.json()["choices"][0]["message"]["content"]
        finish_reason = response.json()["choices"][0]["finish_reason"]
    except KeyError:
        reponse_content = "Ahem le serveur semble inaccessible pour le moment, désolé "
        finish_reason = "error"

    if finish_reason == "length":
        reponse_content += "[...]\n" + "J'ai atteint ma la limite de caractères, désolé !"

    if response.status_code == 200:
        # La requête a réussi
        await request_success(response, reponse_content, origine)
        role = discord.utils.get(origine.guild.roles, id=achievements['jarvis_ach'])
        await origine.author.add_roles(role)
        """if ("Tout de suite Mr.Stark !" in reponse_content):
            role = discord.utils.get(origine.guild.roles, id=jarvis_ach)
            already_found = False
            for member in origine.guild.members:
                if discord.utils.get(member.roles, id=jarvis_ach) is not None:
                    already_found = True
            await origine.author.add_roles(role)
            if not already_found:
                channel = client.get_channel(id_salon_achievements)
                await channel.send(f"L'achievement {role.mention} a été découvert par {origine.author.mention} !")"""
    else:
        # Gérer les échecs ou les erreurs
        await request_failure(response, reponse_content, origine);


async def trigger_jarvis(message):
    messages = []
    if message and message.reference is not None:
        message_resolved = await message.channel.fetch_message(message.reference.message_id)
        heure = message.reference.resolved.created_at
        heure_montreal = heure.astimezone(pytz.timezone('America/Montreal'))
        contenu = "SYSTEM : system : L'utilisateur en question fait référence au message suivant -> \"" \
                  + message_resolved.content + "\" écrit par \"" \
                  + message_resolved.author.name + "\" le " \
                  + message_resolved.created_at.strftime("%d/%m/%Y à %H:%M:%S")
        contenu = contenu.replace("CEGEP-BOT", "Jarvis")
        messages.append(contenu + "\n")

    messages_raw = []
    messages = []

    async for msg in message.channel.history(limit=10):
        messages_raw.append(msg)

    messages_to_process = []
    for msg in messages_raw:
        if msg.content.startswith("/jarjarclearmemory"):
            break
        messages_to_process.append(msg)

    for msg in messages_to_process:
        contenu = msg.created_at.strftime("%d/%m/%Y à %H:%M:%S") + " " + msg.author.name + " a écrit : " + msg.content
        contenu = contenu.replace("CEGEP-BOT", "Jarvis")
        messages.append(contenu + "\n")

        if msg.reference is not None:
            message_resolved = await msg.channel.fetch_message(msg.reference.message_id)
            contenu = "SYSTEM : system : Le message SUIVANT est en réponse à ce message -> \"" \
                      + message_resolved.content + "\" écrit par \"" \
                      + message_resolved.author.name + "\""
            contenu = contenu.replace("CEGEP-BOT", "Jarvis")
            messages.append(contenu + "\n")
    print(messages)

    # Si le channel est le salon "id_salons_jarvis_testeur"
    if message.channel == client.get_channel(salons['id_salon_jarvis_testeur']):
        global prompt_test
        print("prompt test : " + prompt_test)
        messages = await messages_formater(messages, prompt_test)
    else:
        messages = await messages_formater(messages)
    await get_completion(messages, 0.8, message)


async def request_failure(urlrequest, reponse_content, origine):
    print("request_failure")
    print(urlrequest)
    print(reponse_content)
    await origine.channel.send(reponse_content)


async def request_success(urlrequest, reponse_content, origine):
    print("request_success")
    reponse_content.replace("@everyone", "@ everyone")
    reponse_content.replace("@here", "@ here")
    print(urlrequest)
    print(reponse_content)
    await origine.channel.send(reponse_content)


async def check_films():
    print("check_films")
    # Récuperer la liste des films au cinéma
    # Flux RSS :
    url = "https://www.cinemagaiete.com/feed/"
    feed = feedparser.parse(url)
    print(feed)
    films = feed.entries

    if await has_changed(films):
        await store_films_in_file(films)
    else:
        # Reschedule myself in 15 minutes
        scheduler.add_job(check_films, 'date',
                          run_date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 900)))
        return

    list_message = []

    # Récuperer le channel
    channel = client.get_channel(salons['id_salon_film'])
    # (channel = client.get_channel(id_salon_bots)
    list_reaction_jour = []

    for film in films:
        message = ""

        # Si le titre en minuscule contient "offre", publicité" ou "promo" on arrête
        if "offre" in film.title.lower() or "publicité" in film.title.lower() or "promo" in film.title.lower():
            break

        link = film.link
        print("film.link : " + link)
        description = html.unescape(film.description)

        # Si la description est vide, on passe au film suivant
        if description == "":
            continue

        contenu = await get_html(link)
        soup = BeautifulSoup(contenu, 'html.parser')
        # print(soup.prettify())

        # Trouver l'élément img
        # Utiliser un sélecteur CSS plus précis pour cibler l'élément img
        img_element = soup.select_one('.attachment-cine-thumbthumb.wp-post-image')
        image_url = img_element['src']
        print(image_url)

        print("image_url : " + image_url)

        titre = "**" + film.title.upper() + "**"
        list_message.append(titre)
        image = "\n" + image_url
        list_message.append(image)
        # message += "\n" + "*" + description + "*"
        # message += "\n" + "||" + "[+](" + link + ")" + "||"
        # listMessage.append(message)

        # Trouver l'élément avec la date "Dès le"
        date_element = soup.select_one('p:-soup-contains("Dès le")')
        date = ""
        if date_element is not None:
            date = date_element.text.strip()
            date = date.title()
            date = date.replace("Le", "le")
            print("date" + date)

            representations = "**" + date + "**" + "\n"
            print("représentations date : " + representations)

        genre = ""
        duree = ""
        if not "A Venir" in date:
            # Trouver l'élément avec le genre
            genre_element = soup.select_one('p:-soup-contains("Genre :")')
            try:
                genre += genre_element.text.strip()
            except:
                genre += "Genre : Non spécifié"
            print(genre)
            representations += genre + "\n"

            # Trouver l'élément avec la durée
            duree_element = soup.select_one('p:-soup-contains("Durée :")')
            try:
                duree += duree_element.text.strip()
            except:
                duree += "Duree : Non spécifié"
            print(duree)
            representations += duree + "\n"

            # Trouver l'élément avec les représentations
            representations_element = soup.select_one('strong:-soup-contains("Représentation :")')
            # Tant que l'élément suivant contient un jour de la semaine, on ajoute le texte à la variable
            # representations

            jours_semaine = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
            try:
                representations_element = representations_element.find_next_sibling("p")
            except:
                synopsis_element = soup.select_one('strong:-soup-contains("Synopsis :")')
                synopsis = synopsis_element.find_next_sibling("p").text.strip()
                print(synopsis)
                representations += "\n" + "*" + synopsis + "*"
                list_message.append(representations)
                list_reaction_jour.append([])
                continue
            representations_jours = []

            while any(jour in representations_element.text.strip() for jour in jours_semaine):
                # Prendre seulement la première ligne
                jours = representations_element.text.strip().split("\n")[0]
                heures = representations_element.text.strip().split("\n")[1]
                representations += jours.title() + " - " + heures + "\n"

                # Séparer les jours et les ajouter à la liste
                jours = jours.split(" ")
                print("jour_semaine : " + str(jours_semaine))
                for jour in jours:
                    if jour in jours_semaine:
                        print("jour " + jour + " est dans jours_semaine")
                        representations_jours.append(jour)
                    else:
                        print("jour " + jour + " n'est pas dans jours_semaine")

                representations_element = representations_element.find_next_sibling("p")

            print(representations)
            # Ajouter les réactions
            list_reaction_jour.append(representations_jours)

        synopsis_element = soup.select_one('strong:-soup-contains("Synopsis :")')
        synopsis = synopsis_element.find_next_sibling("p").text.strip()
        print(synopsis)
        representations += "\n" + "*" + synopsis + "*"
        list_message.append(representations)

    nouveaux_films_messages = "# ------ Semaine du " + time.strftime("%d/%m/%Y") + " ------ #" + "\n" + html.unescape(
        "\u200B")
    await channel.send(nouveaux_films_messages)
    for message in list_message:
        # Tous les 3 messages, et si le message n'est pas le dernier, on ajoute un saut de ligne et une réaction
        is_end_film = (list_message.index(message) + 1) % 3 == 0
        if is_end_film and list_message.index(message) != len(list_message) - 1:
            # message += "\n" + html.unescape("\u200B")
            print()
        sent_message = await channel.send(message)
        if is_end_film:
            await sent_message.add_reaction("✋")
            try:
                list_jour = list_reaction_jour.pop(0)
                for jour in list_jour:
                    await add_day_reaction(sent_message, jour)
            except IndexError:
                pass

    role = discord.utils.get(channel.guild.roles, id=roles['role_cinephile'])
    last_message = f"{role.mention} \nDe nouveaux films sont disponibles !"
    last_message += "\n\n" + ":popcorn: Tu va voir un film ? Fait le savoir ✋ !"
    last_message += "\n\n" + "*Tu veux être notifié des nouveaux films ? Abonne toi ! :bell:*"
    last_sent_message = await channel.send(last_message)
    await last_sent_message.add_reaction("🔔")


async def store_films_in_file(films):
    print("store_films_in_file")
    # Ouvrir le fichier en mode écriture
    with open("films.txt", "w", encoding="utf-8") as file:
        # Écrire chaque film dans le fichier
        for film in films:
            file.write(film.title + "\n")
            file.write(film.link + "\n")
            file.write(film.description + "\n")
            file.write("\n")


async def has_changed(films):
    print("has_changed")
    # Si le fichier n'existe pas, on le crée
    if not os.path.exists("films.txt"):
        return True
    # Ouvrir le fichier en mode lecture
    with open("films.txt", "r", encoding="utf-8") as file:
        # Lire le contenu du fichier
        file_content = file.read()
        # Si le contenu du fichier est différent de la liste des films

        expected_content = ""
        for film in films:
            expected_content += film.title + "\n"
            expected_content += film.link + "\n"
            expected_content += film.description + "\n"
            expected_content += "\n"

        if file_content != expected_content:
            return True
        return False

async def get_html(url):
    # Envoyez une requête HTTP GET pour obtenir le contenu de la page
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(response.status_code)
    return response.text


async def add_day_reaction(message, jour):
    if jour == "LUNDI":
        await message.add_reaction("🇱")
    elif jour == "MARDI":
        await message.add_reaction("🇲")
    elif jour == "MERCREDI":
        await message.add_reaction("Ⓜ️")
    elif jour == "JEUDI":
        await message.add_reaction("🇯")
    elif jour == "VENDREDI":
        await message.add_reaction("🇻")
    elif jour == "SAMEDI":
        await message.add_reaction("🇸")
    elif jour == "DIMANCHE":
        await message.add_reaction("🇩")
