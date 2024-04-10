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
            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError:
                return 0
            return (await response.json())["id"]


async def get_player_skin(username: str) -> str:
    async with aiohttp.ClientSession() as session:
        player_id = await get_player_id(username)
        if player_id == 0:
            return "https://mineskin.eu/armor/body/Steve/50.png"
        url = f"https://mineskin.eu/armor/body/{player_id}/50.png"
        return url


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


async def edit_join_request(interaction: discord.Interaction, role: discord.Role, skin_url: str, ctx):
    # Get the member who clicked the button
    member = interaction.user

    # Get the original message sent by the bot
    message = await ctx.channel.fetch_message(interaction.message.id)
    embed = discord.Embed(title="Join Request",
                          description=f"C'est tout bon {member} ! Une fois ta demande acceptée, "
                                      f"tu pourras rejoindre le serveur SMP sous le pseudo "
                                      f"\"{message.embeds[0].title}\" en tant que {role.mention}.",
                          color=discord.Color.blue())
    embed.set_thumbnail(url=skin_url)
    embed.set_footer(text="... En attente de validation ...")
    await message.edit(embed=embed, view=None)


async def join_request(ctx, pseudo_minecraft: str):
    # Si le joueur a déjà un des 2 rôles, on refuse la demande
    role_pacifiste = discord.utils.get(ctx.guild.roles, id=roles["pacifiste"])
    role_survivant = discord.utils.get(ctx.guild.roles, id=roles["survivant"])
    if role_pacifiste in ctx.author.roles or role_survivant in ctx.author.roles:
        await ctx.send(
            f"{ctx.author.mention}, tu as déjà rejoint le serveur SMP. Si tu veux changer de faction, contacte un modérateur.")
        return

    skin_url = await get_player_skin(pseudo_minecraft)
    message = f"Salut {ctx.author.mention}, tu veux rejoindre le serveur SMP avec le pseudo Minecraft \"{pseudo_minecraft}\"."
    embed = discord.Embed(title="Join Request", description=message, color=discord.Color.blue())
    embed.set_thumbnail(url=skin_url)
    embed.set_footer(text="Choisis ta faction pour commencer l'aventure !")

    # Create a View instance with a timeout of 3 minutes
    view = discord.ui.View(timeout=180.0)

    # Create a Button instance for the Pacifiste role
    pacifiste_button = discord.ui.Button(label="Pacifiste", style=discord.ButtonStyle.blurple, custom_id="pacifiste")
    pacifiste_button.callback = lambda interaction: edit_join_request(interaction, role_pacifiste, skin_url, ctx)
    view.add_item(pacifiste_button)

    # Create a Button instance for the Survivant role
    survivant_button = discord.ui.Button(label="Survivant", style=discord.ButtonStyle.green, custom_id="survivant")
    survivant_button.callback = lambda interaction: edit_join_request(interaction, role_survivant, skin_url, ctx)
    view.add_item(survivant_button)

    print(embed.to_dict())

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
