import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

KEYWORDS = ["唱歌", "恭喜發財", "劉德華", "新年快樂"]
MP3_PATH = "MayYouBeProsperous.mp3"


def find_active_voice_channel(guild: discord.Guild):
    for channel in guild.voice_channels:
        if len(channel.members) > 0:
            return channel
    return None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not any(keyword in message.content for keyword in KEYWORDS):
        return

    if not message.guild:
        return

    if not os.path.isfile(MP3_PATH):
        await message.channel.send("找不到音檔")
        return

    voice_channel = find_active_voice_channel(message.guild)
    if not voice_channel:
        await message.channel.send("目前沒有任何人在語音頻道")
        return

    vc = message.guild.voice_client
    if vc and vc.is_connected():
        return

    vc = await voice_channel.connect()

    source = discord.FFmpegPCMAudio(MP3_PATH, options="-vn")
    vc.play(source)

    while vc.is_playing():
        await asyncio.sleep(0.5)

    await vc.disconnect()

    await bot.process_commands(message)

bot.run(token)