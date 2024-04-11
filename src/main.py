# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
import json
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from discord import default_permissions
from pytz import timezone

import discord
from discord.ext import commands

from src import bot_commands
from src import minecraft

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
# bot = commands.Bot(command_prefix='$', intents=intents)
bot = discord.Bot(intents=intents)

# bot = discord.bot(intents=intents)
# ot = discord.Bot(command_prefix='/', intents=intents)


with open('src/salons.json') as f:
    salons = json.load(f)

with open('src/roles.json') as f:
    roles = json.load(f)

with open('src/achievements.json') as f:
    achievements = json.load(f)

with open('src/misc.json') as f:
    misc = json.load(f)

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


async def get_role_from_payload(payload, user):
    if payload.emoji.name == "💻":
        return discord.utils.get(user.guild.roles, id=roles['informatique'])
    elif payload.emoji.name == "📁":
        return discord.utils.get(user.guild.roles, id=roles['multimedia'])
    elif payload.emoji.name == "📷":
        return discord.utils.get(user.guild.roles, id=roles['photographie'])
    elif payload.emoji.name == "🌐":
        return discord.utils.get(user.guild.roles, id=roles['A3SI'])
    elif payload.emoji.name == "⚡":
        return discord.utils.get(user.guild.roles, id=roles['TGEAC'])
    elif payload.emoji.name == "💟":
        return discord.utils.get(user.guild.roles, id=roles['soins_infirmier'])
    elif payload.emoji.name == "🦷":
        return discord.utils.get(user.guild.roles, id=roles['hygiene_dentaire'])
    elif payload.emoji.name == "✈️":
        return discord.utils.get(user.guild.roles, id=roles['tourisme'])
    elif payload.emoji.name == "🌆":
        return discord.utils.get(user.guild.roles, id=roles['urbanisme'])
    elif payload.emoji.name == "📚":
        return discord.utils.get(user.guild.roles, id=roles['arts_lettres'])
    elif payload.emoji.name == "🧬":
        return discord.utils.get(user.guild.roles, id=roles['sciences_humaines'])
    elif payload.emoji.name == "🌿":
        return discord.utils.get(user.guild.roles, id=roles['sciences_nature'])
    elif payload.emoji.name == "🎓":
        return discord.utils.get(user.guild.roles, id=roles['tremplin_DEC'])
    # Localisation
    elif payload.emoji.name == "2️⃣":
        return discord.utils.get(user.guild.roles, id=roles['res2e'])
    elif payload.emoji.name == "3️⃣":
        return discord.utils.get(user.guild.roles, id=roles['res3e'])
    elif payload.emoji.name == "4️⃣":
        return discord.utils.get(user.guild.roles, id=roles['res4e'])
    elif payload.emoji.name == "🇪":
        return discord.utils.get(user.guild.roles, id=roles['res_ext'])
    elif payload.emoji.name == "🏳️‍🌈":
        return discord.utils.get(user.guild.roles, id=roles['LGBT'])
    elif payload.emoji.name == "🌈":
        return discord.utils.get(user.guild.roles, id=roles['Soutien_LGBT'])
    else:
        return None


@bot.event
async def on_raw_reaction_add(payload):
    print("on_raw_reaction_add : " + payload.emoji.name + " " + str(payload.channel_id))
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.member.bot:
        return  # Ignorer les réactions du bot

    if payload.channel_id == salons['id_salon_film'] and payload.emoji.name == "🔔":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=roles['role_cinephile'])
        await user.add_roles(role)

    elif payload.channel_id == salons['id_salon_rules'] and payload.emoji.name == "✅":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=roles['role_rules_temp'])
        await user.add_roles(role)
        # Si l'utilisateur à déjà le rôle temp
        if discord.utils.get(user.guild.roles, id=roles['role_rules_temp']) in user.roles:
            role_1984 = discord.utils.get(user.guild.roles, id=achievements['id_1984'])
            already_found = False
            for member in user.guild.members:
                if discord.utils.get(member.roles, id=achievements['id_1984']) is not None:
                    already_found = True
            await user.add_roles(role_1984)
            if not already_found:
                channel = bot.get_channel(salons['id_salon_achievements'])
                await channel.send(f"L'achievement {role_1984.mention} a été découvert par {user.mention} !")

    elif payload.channel_id == salons['id_salon_roles'] and payload.emoji.name == "💚":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=roles['student'])
        await user.add_roles(role)
        role_ac = discord.utils.get(user.guild.roles, id=roles['role_achievements'])
        await user.add_roles(role_ac)
        # Enlever le rôle temporaire
        role = discord.utils.get(user.guild.roles, id=roles['role_rules_temp'])
        await user.remove_roles(role)

    elif payload.channel_id == salons['id_salon_roles'] and payload.emoji.name == "💙":
        user = payload.member
        role = discord.utils.get(user.guild.roles, id=roles['non_student'])
        await user.add_roles(role)
        role_ac = discord.utils.get(user.guild.roles, id=roles['role_achievements'])
        await user.add_roles(role_ac)
        # Enlever le rôle temporaire
        role = discord.utils.get(user.guild.roles, id=roles['role_rules_temp'])
        await user.remove_roles(role)

    elif payload.channel_id == salons['id_salon_roles']:
        # Add formation
        user = payload.member
        print(payload.emoji.name)
        role = get_role_from_payload(payload, user)
        if role is None:
            return
        print(role)
        await user.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    print("on_raw_reaction_remove")

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    # Vérifiez si la réaction a été ajoutée dans le salon spécifique
    if payload.channel_id == salons['id_salon_film'] and payload.emoji.name == "🔔":
        role = discord.utils.get(user.guild.roles, id=salons['role_cinephile'])
        await user.remove_roles(role)

    elif payload.channel_id == salons['id_salon_roles'] and payload.emoji.name == "💚":
        role = discord.utils.get(user.guild.roles, id=roles['student'])
        await user.remove_roles(role)
        # Si l'utilisateur n'a pas le rôle non étudiant, on lui ajoute le rôle temporaire
        if not discord.utils.get(user.guild.roles, id=roles['non_student']) in user.roles:
            role = discord.utils.get(user.guild.roles, id=roles['role_rules_temp'])
            await user.add_roles(role)

    elif payload.channel_id == salons['id_salon_roles'] and payload.emoji.name == "💙":
        role = discord.utils.get(user.guild.roles, id=roles['non_student'])
        await user.remove_roles(role)
        # Si l'utilisateur n'a pas le rôle étudiant, on lui ajoute le rôle temporaire
        if not discord.utils.get(user.guild.roles, id=roles['student']) in user.roles:
            role = discord.utils.get(user.guild.roles, id=roles['role_rules_temp'])
            await user.add_roles(role)

    # Roles Formation + Localisation
    elif (payload.channel_id == salons['id_salon_roles']):
        role = get_role_from_payload(payload, user)
        if role is None:
            return
        print(role)
        await user.remove_roles(role)


@bot.event
async def on_member_join(member):
    print("on_member_join")
    # Récuperer le channel
    channel = bot.get_channel(salons['id_salon_bienvenue'])

    new_message = f"Salut {member.mention}, bienvenue sur le serveur !"

    await channel.send(new_message)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    # await check_films()
    # schedule pour exécuter la fonction check_films tous les jeudi à 12h
    eastern_tz = timezone('US/Eastern')
    scheduler.configure(timezone=eastern_tz)

    scheduler.add_job(bot_commands.check_films, 'cron', day_of_week='thu', hour=12, minute=0, second=0)
    # Toute les 15 minutes, print logs
    scheduler.add_job(printLogJarvis, 'cron', hour='*/1', minute=0, second=0)
    scheduler.start()

    await bot_commands.importer(bot, salons, roles, achievements, misc, scheduler, openai_token)
    await minecraft.importer(bot)


@bot.event
async def on_message(message):
    dots = ""
    if len(message.content) > 50:
        dots = "[...]"

    if message.reference is not None and message.reference.resolved is not None:
        print("-> En réponse à : " + str(
            message.reference.resolved.author) + " : " + message.reference.resolved.content)

    print("on_message " + str(time.localtime().tm_hour) + "h" + str(time.localtime().tm_min) + " "
          + str(message.author) + " : " + message.content[:50] + dots)
    if message.author == bot.user:
        return

    await bot_commands.commands_manager(message)

    # Si le message a été envoyé entre 2h et 5h du matin
    if 2 <= time.localtime().tm_hour < 5:
        # On regarde parmis tous les membres du serveur si quelqu'un a l'achievement "early bird", si personne ne l'a
        # alors on écrit un message dans le channel des achievements
        already_found = False
        for member in message.guild.members:
            if discord.utils.get(member.roles, id=achievements['night_owl_id']) is not None:
                already_found = True
        # Les admins ne peuvent pas découvrir l'achievement
        if not already_found and discord.utils.get(message.author.roles, id=roles['role_createur']) is not None:
            return
        # Ajouter l'achievement "night owl"
        await message.author.add_roles(message.guild.get_role(achievements['night_owl_id']))
        if not already_found:
            channel = bot.get_channel(salons['id_salon_achievements'])
            role_night_owl = discord.utils.get(message.guild.roles, id=achievements['night_owl_id'])
            await channel.send(f"L'achievement {role_night_owl.mention} a été découvert par {message.author.mention} !")


    # Si le message a été envoyé entre 5h et 8h du matin
    elif 5 <= time.localtime().tm_hour < 8:
        already_found = False
        for member in message.guild.members:
            if discord.utils.get(member.roles, id=achievements['early_bird_id']) is not None:
                already_found = True
        # Les admins ne peuvent pas découvrir l'achievement
        if not already_found and discord.utils.get(message.author.roles, id=roles['role_createur']) is not None:
            return
        # Ajouter l'achievement "early bird"
        await message.author.add_roles(message.guild.get_role(achievements['early_bird_id']))
        if not already_found:
            channel = bot.get_channel(salons['id_salon_achievements'])
            role_early_bird = discord.utils.get(message.guild.roles, id=roles['early_bird_id'])
            await channel.send(
                f"L'achievement {role_early_bird.mention} a été découvert par {message.author.mention} !")

    # await bot.process_commands(message)


async def printLogJarvis():
    print("printLogJarvis")
    channel = bot.get_channel(salons['id_salon_jarvis_logs'])
    # Time + ping + "Jarvis online"
    log = "[" + time.strftime("%H:%M:%S", time.localtime()) + "] - " + str(
        round(bot.latency, 2)) + "ms" + " Jarvis up"
    await channel.send(log)


@bot.command(description="Rejoignez le serveur Minecraft !")
async def joinsmp(ctx, pseudo_minecraft: str):
    await minecraft.join_request(ctx, pseudo_minecraft)

#await minecraft.joinrequest(ctx, pseudo_minecraft, faction)

try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("No discord token found")
    bot.run(token)
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
