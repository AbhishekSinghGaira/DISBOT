import discord
from discord.ext import commands
import wavelink
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}

@bot.event
async def on_ready():
    await wavelink.NodePool.create_node(
        bot=bot,
        host="lavalink.devamop.in",
        port=443,
        password="lavalink",
        https=True
    )
    print(f"Logged in as {bot.user}")

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def play_next(vc, ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await vc.disconnect()
        return

    track = queue.pop(0)
    await vc.play(track)
    await ctx.send(f"🎶 Now Playing: **{track.title}**")

# 🔊 JOIN
@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("Pehle VC join kar")
        return

    if ctx.voice_client:
        await ctx.send("Already VC me hoon")
        return

    await ctx.author.voice.channel.connect(cls=wavelink.Player)
    await ctx.send("VC join kar li 🎧")

# ▶️ PLAY
@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("VC me aa pehle")
        return

    vc: wavelink.Player = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)

    tracks = await wavelink.YouTubeTrack.search(query)
    if not tracks:
        await ctx.send("Song nahi mila 😔")
        return

    queue = get_queue(ctx.guild.id)
    queue.append(tracks[0])

    if not vc.is_playing():
        await play_next(vc, ctx)
    else:
        await ctx.send(f"➕ Added to queue: **{tracks[0].title}**")

# 📃 QUEUE
@bot.command()
async def queue(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await ctx.send("Queue khali hai")
        return

    msg = "\n".join([f"{i+1}. {t.title}" for i, t in enumerate(queue)])
    await ctx.send(f"🎵 **Queue:**\n{msg}")

# ⏭️ SKIP
@bot.command()
async def skip(ctx):
    vc: wavelink.Player = ctx.voice_client
    if vc and vc.is_playing():
        await vc.stop()
        await play_next(vc, ctx)
    else:
        await ctx.send("Kuch play nahi ho raha")

# ⛔ STOP
@bot.command()
async def stop(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()

    vc: wavelink.Player = ctx.voice_client
    if vc:
        await vc.stop()
        await ctx.send("Music stop + queue clear ⛔")

# 🚪 LEAVE
@bot.command()
async def leave(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("VC se nikal gaya 👋")

bot.run(TOKEN)
