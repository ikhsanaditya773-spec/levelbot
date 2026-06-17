import discord
import json
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

XP_FILE = "xp_data.json"

def load_xp():
    if os.path.exists(XP_FILE):
        with open(XP_FILE, "r") as f:
            return json.load(f)
    return {}

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f)

def get_level(xp):
    level = 0
    required = 100
    while xp >= required:
        xp -= required
        level += 1
        required += 50
    return level

LEVEL_UNLOCK = 5
ROLE_NAME = "Level5"

xp_data = load_xp()

@client.event
async def on_ready():
    print(f"Bot online: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    old_xp = xp_data.get(user_id, 0)
    old_level = get_level(old_xp)

    xp_data[user_id] = old_xp + 15
    save_xp(xp_data)

    new_level = get_level(xp_data[user_id])

    if new_level > old_level:
        await message.channel.send(
            f"🎉 {message.author.mention} naik ke **Level {new_level}**!"
        )
        if new_level >= LEVEL_UNLOCK:
            guild = message.guild
            role = discord.utils.get(guild.roles, name=ROLE_NAME)
            if role and role not in message.author.roles:
                await message.author.add_roles(role)
                await message.channel.send(
                    f"🔓 {message.author.mention} unlock channel secret!"
                )

client.run("TOKEN")