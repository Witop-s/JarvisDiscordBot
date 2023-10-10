import asyncio
import json
import os
import time
from urllib.request import Request

import feedparser
import html
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup

import hikari
import lightbulb

intents = hikari.Intents.ALL
intents.message_content = True
intents.members = True

bot = lightbulb.BotApp(
    token=os.getenv("TOKEN"),
    prefix="!",
    intents=intents,
    default_enabled_guilds=(1152496106819821610),
)

id_salon_film = 1154611673844416552
role_cinephile = 1160395562022084652
early_bird_id = 1161104309266681877
night_owl_id = 1161104505631416360

openai_token = os.getenv("OPENAI") or ""

# ------------------------ #
#       Achievements       #
# ------------------------ #


@bot.command()
@lightbulb.command("ping", "Test the bot's latency.")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx):
    print("ping : " + ctx.content)
    await ctx.respond(f'Pong! {round(bot.heartbeat_latency, 1)}ms')


@bot.listen(hikari.StartedEvent)
async def on_ready(event):
    print(f'Bot logged in!')
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_films, 'cron', day_of_week='thu', hour=12)
    scheduler.start()


@bot.listen(hikari.InteractionCreateEvent)
async def on_reaction_add(event: hikari.PresenceUpdateEvent):
    print("on_reaction_add")
    if event.channel_id == id_salon_film:
        if event.member.is_bot:
            return
        if event.emoji.name == "🔔":
            user = event.member
            role = await user.fetch_role(role_cinephile)
            await user.add_role(role)


@bot.event()
async def on_reaction_remove(event: hikari.PresenceUpdateEvent):
    print("on_reaction_remove")
    if event.channel_id == id_salon_film and event.emoji.name == "🔔":
        guild = await bot.rest.fetch_guild(event.guild_id)
        user = await guild.fetch_member(event.user_id)
        role = await guild.fetch_role(role_cinephile)
        await user.remove_role(role)


@bot.event()
async def on_message_create(event: hikari.MessageCreateEvent):
    if event.message.author == bot.me:
        return

    if event.message.author.is_bot:
        return

    if "jarvis" in event.message.content.lower():
        async with event.message.channel.typing():
            await trigger_jarvis(event.message)

    role = await event.guild.fetch_role(night_owl_id)
    if 2 <= time.localtime().tm_hour <= 5:
        await event.message.author.add_role(role)

    role = await event.guild.fetch_role(early_bird_id)
    if 5 <= time.localtime().tm_hour <= 8:
        await event.message.author.add_role(role)


async def trigger_jarvis(message):
    messages = []
    async for msg in message.channel.fetch_messages(limit=5):
        content = msg.author.username + " - " + msg.content
        messages.append(content + "\n")
    print(messages)
    await get_completion(messages, 0.8, message)


@bot.command()
async def check_films(ctx):
    url = "https://www.cinemagaiete.com/feed/"
    feed = feedparser.parse(url)
    films = feed.entries

    list_message = []
    channel = await ctx.guild.fetch_channel(id_salon_film)
    list_reaction_jour = []

    for film in films:
        message = ""

        if "offre" in film.title.lower() or "publicité" in film.title.lower() or "promo" in film.title.lower():
            break

        link = film.link
        description = html.unescape(film.description)

        if description == "":
            continue

        contenu = await get_html(link)
        soup = BeautifulSoup(contenu, 'html.parser')
        img_element = soup.select_one('.attachment-cine-thumbthumb.wp-post-image')
        image_url = img_element['src']
        print(image_url)

        titre = "**" + film.title.upper() + "**"
        list_message.append(titre)
        image = "\n" + image_url
        list_message.append(image)

        date_element = soup.select_one('p:-soup-contains("Dès le")')
        date = date_element.text.strip()
        date = date.title()
        date = date.replace("Le", "le")
        print("date" + date)

        representations = "**" + date + "**" + "\n"
        print("représentations date : " + representations)
        if not "A Venir" in date:
            genre_element = soup.select_one('p:-soup-contains("Genre :")')
            genre = genre_element.text.strip()
            print(genre)

            duree_element = soup.select_one('p:-soup-contains("Durée :")')
            duree = duree_element.text.strip()
            print(duree)

            representations_element = soup.select_one('strong:-soup-contains("Représentation :")')
            jours_semaine = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
            representations_element = representations_element.find_next_sibling("p")
            representations_jours = []

            while any(jour in representations_element.text.strip() for jour in jours_semaine):
                jours = representations_element.text.strip().split("\n")[0]
                heures = representations_element.text.strip().split("\n")[1]
                representations += jours.title() + " - " + heures + "\n"

                jours = jours.split(" ")
                for jour in jours:
                    if jour in jours_semaine:
                        representations_jours.append(jour)

                representations_element = representations_element.find_next_sibling("p")

            print(representations)
            list_reaction_jour.append(representations_jours)

        synopsis_element = soup.select_one('strong:-soup-contains("Synopsis :")')
        synopsis = synopsis_element.find_next_sibling("p").text.strip()
        print(synopsis)
        representations += "\n" + "*" + synopsis + "*"
        list_message.append(representations)

    for message in list_message:
        is_end_film = (list_message.index(message) + 1) % 3 == 0
        if is_end_film and list_message.index(message) != len(list_message) - 1:
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

    role = await channel.guild.fetch_role(role_cinephile)
    last_message = f"{role.mention} \nDe nouveaux films sont disponibles !"
    last_message += "\n\n" + ":popcorn: Tu vas voir un film ? Fais-le savoir ✋ !"
    last_message += "\n\n" + "*Tu veux être notifié des nouveaux films ? Abonne-toi ! :bell:*"
    last_sent_message = await channel.send(last_message)
    await last_sent_message.add_reaction("🔔")


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


async def get_html(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(response.status_code)
    return response.text


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

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    reponse_content = response.json()["choices"][0]["message"]["content"]

    if response.status_code == 200:
        await on_success(response, reponse_content, origine)
    else:
        await on_failure(response, reponse_content)


async def on_success(urlrequest, reponse_content, origine):
    print("on_success")
    print(urlrequest)
    print(reponse_content)
    await origine.channel.send(reponse_content)


async def on_failure(urlrequest, reponse_content):
    print("on_failure")
    print(urlrequest)
    print(reponse_content)


async def messages_formater(messages):
    messages.reverse()
    messages_formated = []
    system_prompt = ("Tu es un bot discord nommé Jarvis, tu vois en entrée les messages envoyés par les gens ainsi que "
                     "leur pseudos (ex: John - Bonjour), et tu dois simplement répondre à ces messages, tu n'as pas "
                     "besoin d'écrire ton nom.")
    messages_formated.append({"role": "system", "content": system_prompt})
    for message in messages:
        utilisateur = message.split(" - ")[0]
        message = message.split(" - ")[1]
        if utilisateur.lower() == "jarvis":
            messages_formated.append({"role": "assistant", "content": message})
        else:
            messages_formated.append({"role": "user", "content": message})

    return messages_formated


bot.run()
