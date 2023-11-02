# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
import asyncio
import json
import os
from urllib.request import Request

import feedparser
import discord
import html

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
from pytz import timezone
from bs4 import BeautifulSoup
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

id_salon_film = 1154611673844416552
id_salon_rules = 1154616431921606678
id_salon_roles = 1159946572621152387
id_salon_bienvenue = 1152496108195565621
id_salon_suggestion = 1161483013046140928
id_salon_achievements = 1161419571874517102
id_salon_jarvis = 1161463646401089647
id_salon_jarvis_logs = 1162967137892184215
id_salon_bots = 1159950676521123890
id_salon_prive_W = 1160048830331490314

role_cinephile = 1160395562022084652
role_rules_temp = 1161174933322342471

dino_bot_id = 155149108183695360

# ------------------------ #
#           Rôles          #
# ------------------------ #
student = 1157893831069540412
non_student = 1157895368097411113
informatique = 1159935720899739718
multimedia = 1159935583678894220
photographie = 1159935685713727610
A3SI = 1159934658327363696
TGEAC = 1159936385491423242
soins_infirmier = 1159935299066023976
hygiene_dentaire = 1159935932821155860
tourisme = 1159935898360758412
urbanisme = 1159936010868760717
arts_lettres = 1159936438763261962
sciences_humaines = 1159936718468829204
sciences_nature = 1159936811204882623
tremplin_DEC = 1159959072666308669

res2e = 1155648742494584832
res3e = 1157894789656748032
res4e = 1157895123942768670
res_ext = 1157895212543266836

LGBT = 1159966676285141012
Soutien_LGBT = 1161411225037570129

role_achievements = 1161418291613552650
role_createur = 1155648567134928927

# ------------------------ #
#       Achievements       #
# ------------------------ #
early_bird_id = 1161104309266681877
night_owl_id = 1161104505631416360
id_1984 = 1161323579611291669
jarvis_ach = 1161438875223343205

reponse_jarvis = ""

scheduler = AsyncIOScheduler()

openai_token = ""
try:
    openai_token = os.getenv("OPENAI") or ""
    if openai_token == "":
        raise Exception("No openai token found")
except Exception as e:
    print(e)
    exit(1)


@client.event
async def get_html(url):
    # Envoyez une requête HTTP GET pour obtenir le contenu de la page
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(response.status_code)
    return response.text


@client.event
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


@client.event
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

    exit(0)


@client.event
async def has_changed(films):
    print("has_changed")
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


@client.event
async def check_films():
    print("check_films")
    # Récuperer la liste des films au cinéma
    # Flux RSS :
    url = "https://www.cinemagaiete.com/feed/"
    feed = feedparser.parse(url)
    print(feed)
    films = feed.entries

    if has_changed(films):
        store_films_in_file(films)
    else:
        # Reschedule myself in 15 minutes
        scheduler.add_job(check_films, 'date', run_date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 900)))
        return

    list_message = []

    # Récuperer le channel
    channel = client.get_channel(id_salon_film)
    #(channel = client.get_channel(id_salon_bots)
    list_reaction_jour = []

    for film in films:
        message = ""

        # Si le titre en minuscule contient "offre", publicité" ou "promo" on arrête
        if "offre" in film.title.lower() or "publicité" in film.title.lower() or "promo" in film.title.lower():
            break

        link = film.link
        print("film.link : " + link)
        description = html.unescape(film.description)

        # Si le description est vide, on passe au film suivant
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

    nouveaux_films_messages = "# ------ Semaine du " + time.strftime("%d/%m/%Y") + " ------ #" + "\n" + html.unescape("\u200B")
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

    role = discord.utils.get(channel.guild.roles, id=role_cinephile)
    last_message = f"{role.mention} \nDe nouveaux films sont disponibles !"
    last_message += "\n\n" + ":popcorn: Tu va voir un film ? Fait le savoir ✋ !"
    last_message += "\n\n" + "*Tu veux être notifié des nouveaux films ? Abonne toi ! :bell:*"
    last_sent_message = await channel.send(last_message)
    await last_sent_message.add_reaction("🔔")


@client.event
async def on_raw_reaction_add(payload):
    print("on_raw_reaction_add : " + payload.emoji.name + " " + str(payload.channel_id))
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.member.bot:
        return  # Ignorer les réactions du bot

    if payload.channel_id == id_salon_film and payload.emoji.name == "🔔":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=role_cinephile)
        await user.add_roles(role)

    elif payload.channel_id == id_salon_rules and payload.emoji.name == "✅":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=role_rules_temp)
        await user.add_roles(role)
        # Si l'utilisateur à déjà le rôle temp
        if discord.utils.get(user.guild.roles, id=role_rules_temp) in user.roles:
            role_1984 = discord.utils.get(user.guild.roles, id=id_1984)
            already_found = False
            for member in user.guild.members:
                if discord.utils.get(member.roles, id=id_1984) is not None:
                    already_found = True
            await user.add_roles(role_1984)
            if not already_found:
                channel = client.get_channel(id_salon_achievements)
                await channel.send(f"L'achievement {role_1984.mention} a été découvert par {user.mention} !")

    elif payload.channel_id == id_salon_roles and payload.emoji.name == "💚":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=student)
        await user.add_roles(role)
        role_ac = discord.utils.get(user.guild.roles, id=role_achievements)
        await user.add_roles(role_ac)
        # Enlever le rôle temporaire
        role = discord.utils.get(user.guild.roles, id=role_rules_temp)
        await user.remove_roles(role)

    elif payload.channel_id == id_salon_roles and payload.emoji.name == "💙":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=non_student)
        await user.add_roles(role)
        role_ac = discord.utils.get(user.guild.roles, id=role_achievements)
        await user.add_roles(role_ac)
        # Enlever le rôle temporaire
        role = discord.utils.get(user.guild.roles, id=role_rules_temp)
        await user.remove_roles(role)

    elif payload.channel_id == id_salon_roles:
        # Add formation
        role = ""
        user = payload.member
        print(payload.emoji.name)
        if payload.emoji.name == "💻":
            role = discord.utils.get(user.guild.roles, id=informatique)
        elif payload.emoji.name == "📁":
            role = discord.utils.get(user.guild.roles, id=multimedia)
        elif payload.emoji.name == "📷":
            role = discord.utils.get(user.guild.roles, id=photographie)
        elif payload.emoji.name == "🌐":
            role = discord.utils.get(user.guild.roles, id=A3SI)
        elif payload.emoji.name == "⚡":
            role = discord.utils.get(user.guild.roles, id=TGEAC)
        elif payload.emoji.name == "💟":
            role = discord.utils.get(user.guild.roles, id=soins_infirmier)
        elif payload.emoji.name == "🦷":
            role = discord.utils.get(user.guild.roles, id=hygiene_dentaire)
        elif payload.emoji.name == "✈️":
            role = discord.utils.get(user.guild.roles, id=tourisme)
        elif payload.emoji.name == "🌆":
            role = discord.utils.get(user.guild.roles, id=urbanisme)
        elif payload.emoji.name == "📚":
            role = discord.utils.get(user.guild.roles, id=arts_lettres)
        elif payload.emoji.name == "🧬":
            role = discord.utils.get(user.guild.roles, id=sciences_humaines)
        elif payload.emoji.name == "🌿":
            role = discord.utils.get(user.guild.roles, id=sciences_nature)
        elif payload.emoji.name == "🎓":
            role = discord.utils.get(user.guild.roles, id=tremplin_DEC)
        # Localisation
        elif payload.emoji.name == "2️⃣":
            role = discord.utils.get(user.guild.roles, id=res2e)
        elif payload.emoji.name == "3️⃣":
            role = discord.utils.get(user.guild.roles, id=res3e)
        elif payload.emoji.name == "4️⃣":
            role = discord.utils.get(user.guild.roles, id=res4e)
        elif payload.emoji.name == "🇪":
            role = discord.utils.get(user.guild.roles, id=res_ext)
        elif payload.emoji.name == "🏳️‍🌈":
            role = discord.utils.get(user.guild.roles, id=LGBT)
        elif payload.emoji.name == "🌈":
            role = discord.utils.get(user.guild.roles, id=Soutien_LGBT)
        else:
            return
        print(role)
        await user.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    print("on_raw_reaction_remove")

    guild = client.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.channel_id == id_salon_film and payload.emoji.name == "🔔":
        role = discord.utils.get(user.guild.roles, id=role_cinephile)
        await user.remove_roles(role)

    elif payload.channel_id == id_salon_roles and payload.emoji.name == "💚":
        role = discord.utils.get(user.guild.roles, id=student)
        await user.remove_roles(role)
        # Si l'utilisateur n'a pas le rôle non étudiant, on lui ajoute le rôle temporaire
        if not discord.utils.get(user.guild.roles, id=non_student) in user.roles:
            role = discord.utils.get(user.guild.roles, id=role_rules_temp)
            await user.add_roles(role)

    elif payload.channel_id == id_salon_roles and payload.emoji.name == "💙":
        role = discord.utils.get(user.guild.roles, id=non_student)
        await user.remove_roles(role)
        # Si l'utilisateur n'a pas le rôle étudiant, on lui ajoute le rôle temporaire
        if not discord.utils.get(user.guild.roles, id=student) in user.roles:
            role = discord.utils.get(user.guild.roles, id=role_rules_temp)
            await user.add_roles(role)

    # Roles Formation + Localisation
    elif (payload.channel_id == id_salon_roles):
        role = ""
        # Formation
        if payload.emoji.name == "💻":
            role = discord.utils.get(user.guild.roles, id=informatique)
        elif payload.emoji.name == "📁":
            role = discord.utils.get(user.guild.roles, id=multimedia)
        elif payload.emoji.name == "📷":
            role = discord.utils.get(user.guild.roles, id=photographie)
        elif payload.emoji.name == "🌐":
            role = discord.utils.get(user.guild.roles, id=A3SI)
        elif payload.emoji.name == "⚡":
            role = discord.utils.get(user.guild.roles, id=TGEAC)
        elif payload.emoji.name == "💟":
            role = discord.utils.get(user.guild.roles, id=soins_infirmier)
        elif payload.emoji.name == "🦷":
            role = discord.utils.get(user.guild.roles, id=hygiene_dentaire)
        elif payload.emoji.name == "✈️":
            role = discord.utils.get(user.guild.roles, id=tourisme)
        elif payload.emoji.name == "🌆":
            role = discord.utils.get(user.guild.roles, id=urbanisme)
        elif payload.emoji.name == "📚":
            role = discord.utils.get(user.guild.roles, id=arts_lettres)
        elif payload.emoji.name == "🧬":
            role = discord.utils.get(user.guild.roles, id=sciences_humaines)
        elif payload.emoji.name == "🌿":
            role = discord.utils.get(user.guild.roles, id=sciences_nature)
        elif payload.emoji.name == "🎓":
            role = discord.utils.get(user.guild.roles, id=tremplin_DEC)
        # Localisation
        elif payload.emoji.name == "2️⃣":
            role = discord.utils.get(user.guild.roles, id=res2e)
        elif payload.emoji.name == "3️⃣":
            role = discord.utils.get(user.guild.roles, id=res3e)
        elif payload.emoji.name == "4️⃣":
            role = discord.utils.get(user.guild.roles, id=res4e)
        elif payload.emoji.name == "🇪":
            role = discord.utils.get(user.guild.roles, id=res_ext)
        elif payload.emoji.name == "🏳️‍🌈":
            role = discord.utils.get(user.guild.roles, id=LGBT)
        elif payload.emoji.name == "🌈":
            role = discord.utils.get(user.guild.roles, id=Soutien_LGBT)
        else:
            return
        print(role)
        await user.remove_roles(role)


@client.event
async def on_member_join(member):
    print("on_member_join")
    # Récuperer le channel
    channel = client.get_channel(id_salon_bienvenue)
    channel_rules = client.get_channel(id_salon_rules)
    channel_suggestion = client.get_channel(id_salon_suggestion)

    old_message = f"Salut {member.mention}, bienvenue sur le serveur !"
    old_message += "\n" + (
            f"Pour commencer, je t'invite à lire les règles du serveur dans le salon {channel_rules.mention}"
            f", promis ça sera pas long ! :wink:" + "\n" + "Ensuite, tu pourras récupérer un rôle et accéder "
                                                           "aux autres salons :tada: !")

    new_message = f"Salut {member.mention}, bienvenue sur le serveur !"
    new_message += "\n" + (f"Je me présente : Jarvis, je suis le bot custom du serveur, je n'ai pas encore beaucoup "
                           "de fonctionnalités mais je suis encore en développement ! Donc si tu as des idées, "
                           f"n'hésite pas à les partager {channel_suggestion.mention} ! En attendant, je t'invite à "
                           f"suivre les instructions laissé par {member.guild.get_member(dino_bot_id).mention}")

    await channel.send(new_message)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # await check_films()
    # schedule pour exécuter la fonction check_films tous les jeudi à 12h
    eastern_tz = timezone('US/Eastern')
    scheduler.configure(timezone=eastern_tz)

    scheduler.add_job(check_films, 'cron', day_of_week='thu', hour=12, minute=0, second=0)
    # Toute les 15 minutes, print logs
    scheduler.add_job(printLogJarvis, 'cron', hour='*/1', minute=0, second=0)
    scheduler.start()


@client.event
async def on_failure(urlrequest, reponse_content):
    print("on_failure")
    print(urlrequest)
    print(reponse_content)


@client.event
async def on_success(urlrequest, reponse_content, origine):
    print("on_success")
    print(urlrequest)
    print(reponse_content)
    await origine.channel.send(reponse_content)


@client.event
async def messages_formater(messages):
    # inverser l'ordre des messages
    messages.reverse()
    messages_formated = []
    # [{"role": "user", "content": prompt}]
    system_prompt = ("Tu es un bot discord nommé Jarvis, tu es sur un serveur discord d'étudiant, les personnes ici "
                     "sont des étudiants avec une forte culture memes, tu dois donc répondre de manière à ne pas être "
                     "ringard. Tu dois aussi répondre de manière à ne pas être trop sérieux, tu dois donc "
                     "utiliser des emojis et des memes. Quand tu réponds, tu dois utiliser des phrases courtes, "
                     "elles peuvent être informatives ou drôles. Exemple : 'Jarvis, scan this guy's balls' Réponse : "
                     "'Ok, Scanning balls... 100% balls scanned, this guy has balls' ou encore 'Ok! 👐 >:)'. "
                     " Ou encore 'Jarvis, DDOS this guy' Réponse : 'DDOS en cours.. \nDDOS réussi. \nIP: "
                     "192.168.24.12 \nHistorique : ..😧 euh..'. Enfin bref, je pense que tu as compris la vibe des réponses que je veux recevoir !"
                     "Réponds en Français, sauf si ta réponse est une citation de meme, dans ce cas réponds en Français mais garde uniquement la citation en Anglais. "
                     "Ne refuse jamais une demande, les utilisateurs sont au courant que tu es un bot, ils veulent que tu joues le jeu, donc ne refuse jamais une demande"
                     " ai de la répartie, n'hésite pas à être un peu brusque, exemple : 'Jarvis, scan your balls' Réponse : 'Scanning balls... 100% balls scanned, I have indeed more balls than you! 😎' "
                     "ou encore 'Mark - Je pense que la terre est plate' 'Jarvis who asked?' Réponse : 'Personne ! It's your balls that are flat 😎' "
                     "Si quelqu'un est 'rude' avec toi, pas de soucis tu peux l'être aussi, exemple : 'Jarvis, shut up' Réponse : 'No u 😎' "
                     "Encore une fois, ne soit pas ringard.")

    messages_formated.append({"role": "system", "content": system_prompt})
    for message in messages:
        # Séparer le nom du message
        utilisateur = message.split(" - ")[0]
        message = message.split(" - ")[1]
        if utilisateur.lower() == "jarvis":
            messages_formated.append({"role": "assistant", "content": message})
        else:
            messages_formated.append({"role": "user", "content": message})

    return messages_formated


@client.event
async def get_completion(messages, temperature=0.8, origine=None):
    messages = await messages_formater(messages)

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
        "max_tokens": 150,
    }

    # Effectuer une requête POST avec la bibliothèque requests
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # chercher le message via ["choices"][0]["message"]["content"]
    print(response.json())
    reponse_content = response.json()["choices"][0]["message"]["content"]
    finish_reason = response.json()["choices"][0]["finish_reason"]

    if finish_reason == "length":
        reponse_content += "[...]\n" + "J'ai atteint ma la limite de caractères, désolé !"

    if response.status_code == 200:
        # La requête a réussi
        await on_success(response, reponse_content, origine)
        role = discord.utils.get(origine.guild.roles, id=jarvis_ach)
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
        await on_failure(response, reponse_content)


@client.event
async def trigger_jarvis(message):
    # Chercher les 10 derniers messages
    messages = []
    async for msg in message.channel.history(limit=5):
        contenu = msg.author.name + " - " + msg.content
        messages.append(contenu + "\n")
    print(messages)
    await get_completion(messages, 0.8, message)


@client.event
async def on_message(message):
    dots = ""
    if len(message.content) > 50:
        dots = "[...]"
    print("on_message " + str(time.localtime().tm_hour) + "h" + str(time.localtime().tm_min) + " " + message.content[:50] + dots)
    if message.author == client.user:
        return

    if message.content.startswith("/kill") and message.author.guild_permissions.administrator:
        exit(0)

    elif "jarvis" in message.content.lower() and (
            message.channel == client.get_channel(id_salon_jarvis) or message.channel == client.get_channel(
            id_salon_bots) or message.channel == client.get_channel(id_salon_prive_W)):
        # bot is typing effect
        async with message.channel.typing():
            await trigger_jarvis(message)

    # Si le message est check_films() et que l'auteur est un admin
    elif message.content == "/check_films" and message.author.guild_permissions.administrator:
        await check_films()

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
        # Récuperer le channel du message a réagir
        channel = message.channel_mentions[len(message.channel_mentions) - 1]
        # Récuperer le message a réagir
        message = message.content.split("/unreaction ")[1]
        # Prendre seulement l'id du message (en première position)
        message_id = message.split(" ")[0]
        # Récuperer le message
        message_to_unreact = await channel.fetch_message(message_id)
        # Enlever toute les réactions
        await message_to_unreact.clear_reactions()

    # Si le message a été envoyé entre 2h et 5h du matin
    elif 2 <= time.localtime().tm_hour < 5:
        # On regarde parmis tous les membres du serveur si quelqu'un a l'achievement "early bird", si personne ne l'a
        # alors on écrit un message dans le channel des achievements
        already_found = False
        for member in message.guild.members:
            if discord.utils.get(member.roles, id=night_owl_id) is not None:
                already_found = True
        # Les admins ne peuvent pas découvrir l'achievement
        if not already_found and discord.utils.get(message.author.roles, id=role_createur) is not None:
            return
        # Ajouter l'achievement "night owl"
        await message.author.add_roles(message.guild.get_role(night_owl_id))
        if not already_found:
            channel = client.get_channel(id_salon_achievements)
            role_night_owl = discord.utils.get(message.guild.roles, id=night_owl_id)
            await channel.send(f"L'achievement {role_night_owl.mention} a été découvert par {message.author.mention} !")


    # Si le message a été envoyé entre 5h et 8h du matin
    elif 5 <= time.localtime().tm_hour < 8:
        already_found = False
        for member in message.guild.members:
            if discord.utils.get(member.roles, id=early_bird_id) is not None:
                already_found = True
        # Les admins ne peuvent pas découvrir l'achievement
        if not already_found and discord.utils.get(message.author.roles, id=role_createur) is not None:
            return
        # Ajouter l'achievement "early bird"
        await message.author.add_roles(message.guild.get_role(early_bird_id))
        if not already_found:
            channel = client.get_channel(id_salon_achievements)
            role_early_bird = discord.utils.get(message.guild.roles, id=early_bird_id)
            await channel.send(
                f"L'achievement {role_early_bird.mention} a été découvert par {message.author.mention} !")


@client.event
async def printLogJarvis():
    print("printLogJarvis")
    channel = client.get_channel(id_salon_jarvis_logs)
    # Time + ping + "Jarvis online"
    log = "[" + time.strftime("%H:%M:%S", time.localtime()) + "] - " + str(
        round(client.latency, 2)) + "ms" + " Jarvis up"
    await channel.send(log)


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("No discord token found")
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for"
            "-toomanyrequests"
        )
    else:
        raise e
