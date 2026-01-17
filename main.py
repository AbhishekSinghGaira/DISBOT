import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True
}

queues = {}  # guild_id : [ (title, url) ]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)

    if not queue:
        await ctx.voice_client.disconnect()
        return

    title, url = queue.pop(0)
    source = discord.FFmpegPCMAudio(url)

    ctx.voice_client.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(ctx), bot.loop
        )
    )

    await ctx.send(f"🎶 Now Playing: **{title}**")

# 🔊 JOIN COMMAND
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.send("Main already VC me hoon 😅")
        else:
            await ctx.author.voice.channel.connect()
            await ctx.send("VC join kar li 🎧")
    else:
        await ctx.send("Pehle tu VC join kar")

# ▶️ PLAY
@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("VC me aa pehle")
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        song = info["entries"][0]
        title = song["title"]
        url = song["url"]

    queue = get_queue(ctx.guild.id)
    queue.append((title, url))

    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"➕ Added to queue: **{title}**")

# 📃 QUEUE
@bot.command()
async def queue(ctx):
    queue = get_queue(ctx.guild.id)

    if not queue:
        await ctx.send("Queue khali hai")
        return

    msg = "\n".join([f"{i+1}. {song[0]}" for i, song in enumerate(queue)])
    await ctx.send(f"🎵 **Queue:**\n{msg}")

# ⏭️ SKIP
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped")
    else:
        await ctx.send("Kuch play nahi ho raha")

# ⛔ STOP
@bot.command()
async def stop(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()

    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Music stop + queue clear ⛔")
    else:
        await ctx.send("Bot VC me nahi hai")

# 🚪 LEAVE
@bot.command()
async def leave(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("VC se nikal gaya 👋")
    else:
        await ctx.send("Already bahar hoon")

bot.run(TOKEN)
