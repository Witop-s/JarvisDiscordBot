import aiohttp


async def get_player_id(username: str) -> int:
    async with aiohttp.ClientSession() as session:
        url = f"https://api.minecraftservices.com/minecraft/profile/lookup/name/{username}"
        async with session.get(url) as response:
            return (await response.json())["id"]


async def get_player_head(username: str) -> str:
    async with aiohttp.ClientSession() as session:
        url = f"https://mineskin.eu/helm/{await get_player_id(username)}/100.png"
        async with session.get(url) as response:
            return (await response.json())["url"]


async def register_user(username: str) -> str:
    player_id = await get_player_id(username)
    player_head = await get_player_head(username)

