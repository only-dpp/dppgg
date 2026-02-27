from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN não encontrado. Verifique seu .env")