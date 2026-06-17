import discord
import json
import os
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ===== LEVEL SYSTEM =====
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

# ===== MUSIC SYSTEM =====
music_queue = []
is_playing = False

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

async def play_next(voice_client):
    global is_playing
    if len(music_queue) > 0:
        is_playing = True
        url = music_queue.pop(0)
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Unknown')
        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(voice_client), client.loop))
    else:
        is_playing = False

@client.event
async def on_ready():
    print(f"Bot online: {client.user}")

@client.event
async def on_message(message):
    global is_playing

    if message.author.bot:
        return

    # ===== XP SYSTEM =====
    user_id = str(message.author.id)
    old_xp = xp_data.get(user_id, 0)
    old_level = get_level(old_xp)
    xp_data[user_id] = old_xp + 15
    save_xp(xp_data)
    new_level = get_level(xp_data[user_id])

    if new_level > old_level:
        await message.channel.send(f"🎉 {message.author.mention} naik ke **Level {new_level}**!")
        if new_level >= LEVEL_UNLOCK:
            guild = message.guild
            role = discord.utils.get(guild.roles, name=ROLE_NAME)
            if role and role not in message.author.roles:
                await message.author.add_roles(role)
                await message.channel.send(f"🔓 {message.author.mention} unlock channel secret!")

    # ===== MUSIC COMMANDS =====
    if message.content.startswith("vplay"):
        if not message.author.voice:
            await message.channel.send("❌ Kamu harus masuk voice channel dulu!")
            return

        query = message.content[5:].strip()
        if not query:
            await message.channel.send("❌ Tulis nama lagu atau URL! Contoh: `vplay Coldplay`")
            return

        voice_channel = message.author.voice.channel
        if message.guild.voice_client is None:
            await voice_channel.connect()
        
        vc = message.guild.voice_client

        # Search YouTube
        if not query.startswith("http"):
            query = f"ytsearch1:{query}"

        music_queue.append(query)
        await message.channel.send(f"🎵 Ditambahkan ke antrian!")

        if not is_playing:
            await play_next(vc)

    elif message.content.startswith("vskip"):
        if message.guild.voice_client and message.guild.voice_client.is_playing():
            message.guild.voice_client.stop()
            await message.channel.send("⏭️ Lagu diskip!")
        else:
            await message.channel.send("❌ Tidak ada lagu yang sedang diputar!")

    elif message.content.startswith("vstop"):
        if message.guild.voice_client:
            music_queue.clear()
            message.guild.voice_client.stop()
            await message.guild.voice_client.disconnect()
            await message.channel.send("⏹️ Musik dihentikan dan bot keluar dari voice channel!")
        else:
            await message.channel.send("❌ Bot tidak ada di voice channel!")

    elif message.content.startswith("vqueue"):
        if len(music_queue) == 0:
            await message.channel.send("📭 Antrian kosong!")
        else:
            q = "\n".join([f"{i+1}. {url}" for i, url in enumerate(music_queue)])
            await message.channel.send(f"📋 **Antrian:**\n{q}")

    elif message.content.startswith("vhelp"):
        await message.channel.send("""
🎵 **Music Commands:**
`vplay [nama/url]` — Play lagu dari YouTube
`vskip` — Skip lagu sekarang
`vstop` — Stop musik & keluar voice channel
`vqueue` — Lihat antrian lagu


⭐ **Level Commands:**
Chat aktif = dapat XP otomatis!
Level 5 = unlock channel secret!
        """)

client.run(os.environ["TOKEN"])
