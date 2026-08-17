import discord
from discord.ext import commands, tasks
from discord import app_commands
import database
import scraper

class AlertBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        database.init_db()
        await self.tree.sync()
        
        # 봇 실행 시 백그라운드 주기적 알림 루프를 실행
        self.check_posts_loop.start()
        print(f"Logged in as {self.user}")

    # 30초 주기
    @tasks.loop(seconds=30)
    async def check_posts_loop(self):
        try:
            posts = await scraper.fetch_recent_posts()
            keywords_data = database.get_all_keywords()
            
            if not posts or not keywords_data:
                return

            for post in posts:
                if database.is_alert_sent(post['id']):
                    continue
                    
                # 신규 게시물인 경우에만 내용을 가져옵니다 (서버 부하 방지)
                content = await scraper.fetch_post_content(post['url'])
                    
                title_lower = post['title'].lower()
                content_lower = content.lower()
                # channel_id별로 전송할 알림 데이터를 집계 (채널별 일괄 전송 및 다수 태그 지원)
                alerts_to_send = {}
                
                for user_id, channel_id, keyword in keywords_data:
                    kw_lower = keyword.lower()
                    if kw_lower in title_lower or kw_lower in content_lower:
                        if channel_id not in alerts_to_send:
                            alerts_to_send[channel_id] = {}
                        if user_id not in alerts_to_send[channel_id]:
                            alerts_to_send[channel_id][user_id] = set()
                        alerts_to_send[channel_id][user_id].add(keyword)
                
                for channel_id, users_data in alerts_to_send.items():
                    channel = self.get_channel(channel_id)
                    if channel is None:
                        try:
                            channel = await self.fetch_channel(channel_id)
                        except Exception:
                            continue
                    
                    if channel:
                        tags = " ".join([f"<@{uid}>" for uid in users_data.keys()])
                        all_kws = set()
                        for kws in users_data.values():
                            all_kws.update(kws)
                        kws_str = ", ".join(all_kws)
                        
                        await channel.send(f"{tags} 🔔 새 게시글 알림 (`{kws_str}`):\n**{post['title']}**\n{post['url']}")
                
                # 중복 마킹은 루프 내 정상 처리된 후 안전하게 반영
                database.mark_alert_sent(post['id'], post['url'])
                
        except Exception as e:
            print(f"Error checking posts: {e}")

    @check_posts_loop.before_loop
    async def before_check_posts_loop(self):
        # 디스코드 게이트웨이 웹소켓이 완전히 연결될 때까지 대기하여 에러를 예방합니다.
        await self.wait_until_ready()

bot = AlertBot()

# --- 슬래시 명령어 구역 ---

@bot.tree.command(name="알림추가", description="특정 키워드 알림을 추가합니다.")
@app_commands.describe(keyword="알림을 받을 키워드")
async def add_alert(interaction: discord.Interaction, keyword: str):
    keyword = keyword.lower().strip()
    success = database.add_keyword(interaction.user.id, interaction.channel_id, keyword)
    if success:
        await interaction.response.send_message(f"✅ '{keyword}' 키워드 알림이 추가되었습니다.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ 이미 등록된 키워드입니다.", ephemeral=True)

@bot.tree.command(name="알림제거", description="등록된 키워드 알림을 제거합니다.")
@app_commands.describe(keyword="제거할 키워드")
async def remove_alert(interaction: discord.Interaction, keyword: str):
    keyword = keyword.lower().strip()
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
