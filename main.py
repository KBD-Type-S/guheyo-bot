import os
import asyncio
from dotenv import load_dotenv
from bot import bot

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

async def main():
    if not TOKEN:
        print("DISCORD_TOKEN is missing. Please set it in .env")
        return
        
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
