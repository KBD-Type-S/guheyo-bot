import os
import asyncio
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import discord

from bot import bot
from database import get_all_keywords, is_alert_sent, mark_alert_sent
import scraper

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

async def check_new_posts():
    try:
        posts = await scraper.fetch_recent_posts()
        keywords_data = get_all_keywords()
        
        for post in posts:
            if is_alert_sent(post['id']):
                continue
                
            title_lower = post['title'].lower()
            notified_channels = set()
            
            for user_id, channel_id, keyword in keywords_data:
                # If keyword matches the post title
                if keyword.lower() in title_lower:
                    if channel_id not in notified_channels:
                        channel = bot.get_channel(channel_id)
                        if channel:
                            await channel.send(f"<@{user_id}> 🔔 새 게시글 알림 (`{keyword}`):\n**{post['title']}**\n{post['url']}")
                            notified_channels.add(channel_id)
            
            mark_alert_sent(post['id'])
            
    except Exception as e:
        print(f"Error checking posts: {e}")

async def main():
    if not TOKEN:
        print("DISCORD_TOKEN is missing. Please set it in .env")
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_new_posts, 'interval', seconds=10)
    scheduler.start()
    
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
