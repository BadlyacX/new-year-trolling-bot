from email.mime import message
import discord
from discord.ext import commands
import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
gemini_api_key = os.getenv("GEMINI_API_KEY")

print("-----------------------Test-----------------------")

print("--------------------------------------------------")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

KEYWORDS = ["唱歌", "恭喜發財", "劉德華", "新年快樂"]
MP3_PATH = "MayYouBeProsperous.mp3"


def find_active_voice_channel(guild: discord.Guild):
    for channel in guild.voice_channels:
        if len(channel.members) > 0:
            return channel
    return None


def generate_text(prompt: str):
    modified_prompt = (
        "你是劉德華，用他的口吻跟粉絲聊天。"
        "回答要自然、親切、有一點幽默，但不要太長。"
        "用繁體中文。"
        f"\n\n粉絲：{prompt}\n劉德華："
    )
    response = model.generate_content(modified_prompt)
    return getattr(response, "text", None)


async def play_audio_once(guild: discord.Guild, text_channel: discord.abc.Messageable):
    if not os.path.isfile(MP3_PATH):
        await text_channel.send("找不到音檔")
        return

    voice_channel = find_active_voice_channel(guild)
    if not voice_channel:
        await text_channel.send("目前沒有任何人在語音頻道")
        return

    vc = guild.voice_client
    if vc and vc.is_connected():
        return

    try:
        vc = await voice_channel.connect()
    except Exception:
        return

    try:
        source = discord.FFmpegPCMAudio(MP3_PATH, options="-vn")
        vc.play(source)

        while vc.is_playing():
            await asyncio.sleep(0.5)
    finally:
        try:
            await vc.disconnect()
        except Exception:
            pass


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    BOT_MENTION_ID = "<@&1463187353626738878>"

    content = message.content or ""

    print(f"[RECV] {message.author} : {content}")

    if BOT_MENTION_ID in content:
        prompt = content.replace(BOT_MENTION_ID, "").strip()

        if not prompt:
            reply_text = "你要講什麼啦～（@我後面加一句話）"
            print(f"[SEND] {reply_text}")
            await message.channel.send(reply_text)
            await bot.process_commands(message)
            return

        try:
            reply = await asyncio.to_thread(generate_text, prompt)
            if reply:
                print(f"[SEND] {reply}")
                await message.channel.send(reply)
            else:
                reply_text = "我剛剛好像卡了一下，等我一下下～"
                print(f"[SEND] {reply_text}")
                await message.channel.send(reply_text)
        except Exception as e:
            print(f"[ERROR] Gemini 呼叫失敗: {e}")
            reply_text = "我現在有點忙，等下再聊～"
            print(f"[SEND] {reply_text}")
            await message.channel.send(reply_text)

        await bot.process_commands(message)
        return

    if any(k in content for k in KEYWORDS):
        print("[VOICE] 關鍵字觸發，準備播放音檔")
        asyncio.create_task(play_audio_once(message.guild, message.channel))

    await bot.process_commands(message)



bot.run(token)


# https://discord.com/oauth2/authorize?client_id=1462766217449312463&scope=bot&permissions=8
