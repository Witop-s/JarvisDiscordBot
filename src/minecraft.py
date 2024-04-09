import json

import aiohttp
import discord
from discord.ext import commands
from discord.ui import Button, View

bot = None

with open('src/salons.json') as f:
    salons = json.load(f)

with open('src/roles.json') as f:
    roles = json.load(f)

async def importer(vBot):
    global bot
    bot = vBot


async def get_player_id(username: str) -> int:
    async with aiohttp.ClientSession() as session:
        url = f"https://api.minecraftservices.com/minecraft/profile/lookup/name/{username}"
        async with session.get(url) as response:
            return (await response.json())["id"]


async def get_player_skin(username: str) -> str:
    async with aiohttp.ClientSession() as session:
        url = f"https://mineskin.eu/armor/body/{await get_player_id(username)}/50.png"
        return url


async def register_user(ctx, username: str) -> str:
    player_id = await get_player_id(username)
    player_head = await get_player_skin(username)
    print(player_id, player_head)
    await ctx.send(f"Player ID: {player_id}\nPlayer Head: {player_head}")


class AcceptDenyView(View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content=f"User has been accepted!", view=None)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content=f"User has been denied!", view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.grey)
    async def annuler(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Action annulée", view=None)


async def add_role_minecraft(interaction: discord.Interaction, role: discord.Role):
    # Get the member who clicked the button
    member = interaction.user

    # Add the role to the member
    await member.add_roles(role)

    # Send a confirmation message
    await interaction.response.send_message(f"{member.mention}, tu as rejoint la faction {role.name} !")

async def edit_join_request(interaction: discord.Interaction, role: discord.Role):
    # Get the member who clicked the button
    member = interaction.user

    # Send a confirmation message
    await interaction.response.send_message(
        f"{member.mention}, ta demande a bien été prise en compte. Tu seras averti dès que tu auras été ajouté à la whitelist.")

    # Edit the original message to show that the request has been processed
    message = await interaction.original_response()
    embed = message.embeds[0]
    embed.set_footer(text=f"{member.name} a rejoint la faction {role.name} !")
    await message.edit(embed=embed, view=None)

async def join_request(ctx, pseudo_minecraft: str):
    skin_url = await get_player_skin(pseudo_minecraft)
    message = f"Salut {ctx.author.mention}, tu veux rejoindre le serveur SMP avec le pseudo Minecraft \"{pseudo_minecraft}\"."
    embed = discord.Embed(title="Join Request", description=message, color=discord.Color.blue())
    embed.set_thumbnail(url=skin_url)
    embed.set_footer(text="Choisis ta faction pour commencer l'aventure !")
    role_pacifiste = discord.utils.get(ctx.guild.roles, id=roles["pacifiste"])
    role_survivant = discord.utils.get(ctx.guild.roles, id=roles["survivant"])
    print(role_pacifiste, role_survivant)

    # Create a View instance with a timeout of 3 minutes
    view = discord.ui.View(timeout=180.0)

    # Create a Button instance for the Pacifiste role
    pacifiste_button = discord.ui.Button(label="Pacifiste", style=discord.ButtonStyle.blurple, custom_id="pacifiste")
    pacifiste_button.callback = lambda interaction: edit_join_request(interaction, role_pacifiste)
    view.add_item(pacifiste_button)

    # Create a Button instance for the Survivant role
    survivant_button = discord.ui.Button(label="Survivant", style=discord.ButtonStyle.green, custom_id="survivant")
    survivant_button.callback = lambda interaction: edit_join_request(interaction, role_survivant)
    view.add_item(survivant_button)

    await ctx.send(embed=embed, view=view)


async def confirm_join(ctx, pseudo_minecraft: str, faction: discord.Role):
    skin_url = await get_player_skin(pseudo_minecraft)
    message = f"@{ctx.author.display_name} veux rejoindre le serveur SMP avec le pseudo Minecraft \"{pseudo_minecraft}\" et la faction {faction.mention}."
    embed = discord.Embed(title="Join Request", description=message, color=discord.Color.blue())
    embed.set_thumbnail(url=skin_url)
    embed.set_footer(text="Cliquer sur les boutons pour accepter ou refuser la demande.")
    view = AcceptDenyView()
    await ctx.send(embed=embed, view=view)

# @bot.command(description="Sends the bot's latency.")  # this decorator makes a slash command
# async def ping(ctx):  # a slash command will be created with the name "ping"
#    await ctx.respond(f"Pong! Latency is {bot.latency}")
