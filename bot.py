import discord
from discord.ext import commands
from discord import app_commands
import database

class AlertBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        database.init_db()
        await self.tree.sync()
        print(f"Logged in as {self.user}")

bot = AlertBot()

@bot.tree.command(name="알림추가", description="특정 키워드 알림을 추가합니다.")
@app_commands.describe(keyword="알림을 받을 키워드")
async def add_alert(interaction: discord.Interaction, keyword: str):
    keyword = keyword.lower()
    success = database.add_keyword(interaction.user.id, interaction.channel_id, keyword)
    if success:
        await interaction.response.send_message(f"✅ '{keyword}' 키워드 알림이 추가되었습니다.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ 이미 등록된 키워드입니다.", ephemeral=True)

@bot.tree.command(name="알림제거", description="등록된 키워드 알림을 제거합니다.")
@app_commands.describe(keyword="제거할 키워드")
async def remove_alert(interaction: discord.Interaction, keyword: str):
    keyword = keyword.lower()
    success = database.remove_keyword(interaction.user.id, interaction.channel_id, keyword)
    if success:
        await interaction.response.send_message(f"🗑️ '{keyword}' 키워드 알림이 제거되었습니다.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ 등록되지 않은 키워드입니다.", ephemeral=True)

@bot.tree.command(name="키워드목록", description="현재 등록된 내 키워드 목록을 확인합니다.")
async def list_keywords(interaction: discord.Interaction):
    keywords = database.get_user_keywords(interaction.user.id, interaction.channel_id)
    if keywords:
        kw_list = "\n".join(f"- {kw}" for kw in keywords)
        await interaction.response.send_message(f"📋 **등록된 키워드 목록:**\n{kw_list}", ephemeral=True)
    else:
        await interaction.response.send_message("등록된 키워드가 없습니다.", ephemeral=True)

@bot.tree.command(name="키워드전체삭제", description="등록된 모든 키워드 알림을 제거합니다.")
async def remove_all_alerts(interaction: discord.Interaction):
    deleted_count = database.remove_all_keywords(interaction.user.id, interaction.channel_id)
    if deleted_count > 0:
        await interaction.response.send_message(f"🗑️ 총 {deleted_count}개의 키워드 알림이 삭제되었습니다.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ 삭제할 키워드가 없습니다.", ephemeral=True)
