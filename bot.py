import sys
import discord
from discord.ext import commands

from config import DISCORD_TOKEN

sys.stdout.reconfigure(encoding="utf-8")

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

EXTENSIONS = [
    "cogs.help",
    "cogs.profile",
    "cogs.patch",
    "cogs.link",
]

@bot.event
async def on_ready():
    # Carrega extensões
    for ext in EXTENSIONS:
        try:
            if ext not in bot.extensions:
                await bot.load_extension(ext)
        except Exception as e:
            print(f"❌ Falha ao carregar {ext}: {e}")

    # Sincroniza comandos
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados:")
        for cmd in synced:
            print(f" - /{cmd.name} → {cmd.description}")
    except Exception as e:
        print(f"❌ Falha ao sincronizar comandos: {e}")

    print("🤖 Bot online!")

bot.run(DISCORD_TOKEN)