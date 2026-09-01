import discord
from discord.ext import commands, tasks
import database
from datetime import datetime
import asyncio

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Khởi động vòng lặp tự động cập nhật mỗi 1 giờ
        self.update_leaderboard_loop.start()

    def cog_unload(self):
        self.update_leaderboard_loop.cancel()

    # =========================================================================
    # HÀM BỔ TRỢ: TẠO NỘI DUNG TIN NHẮN VĂN BẢN THƯỜNG
    # =========================================================================
    async def create_leaderboard_text(self):
        """Hàm lấy dữ liệu từ DB và tạo chuỗi văn bản thường chuẩn Markdown"""
        # Lấy dữ liệu top 10 từ database
        top_players = database.get_top_bakers(10)

        # Khởi tạo phần đầu của tin nhắn
        msg_content = (
            "# <:cupsk:1543848383456739391> **BẢNG XẾP HẠNG** <:cupsk:1543848383456739391>\n"
            "Dưới đây là danh sách Top 10 người có số lượng **Hộp Bánh Trung Thu** đã ghép nhiều nhất Server!\n"
            "<a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371>\n"
        )

        if not top_players:
            msg_content += "\n*Hiện tại chưa có ai ghép thành công Hộp Bánh nào cả. Hãy là người đầu tiên!*\n"
        else:
            medal_emojis = {1: "<a:medal1:1523749987433975899>", 2: "<a:medal2:1523749990126714891>", 3: "<a:medal3:1523749992819456000>"}

            for index, (user_id, count) in enumerate(top_players, start=1):
                emoji = medal_emojis.get(index, f"`#{index}` ")
                
                # Tìm tên hiển thị của User
                try:
                    user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    user_name = user.display_name if user else f"Người dùng ẩn ({user_id})"
                except:
                    user_name = f"Người dùng ({user_id})"

                # Định dạng dòng chữ thường
                if index == 1:
                    msg_content += f"### {emoji} **{user_name}** — `{count} Hộp` <a:cutecrown:1543839336582226000>\n"
                else:
                    msg_content += f"{emoji} {user_name} — `{count} Hộp`\n"

        msg_content += "<a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371><a:line:1544173448786616371>\n"
        
        # Thêm thời gian cập nhật ở cuối tin nhắn (thay thế cho footer cũ)
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        msg_content += f"*-# <a:load:1543848338057592863> Tự động cập nhật sau mỗi 1 giờ • Lần cuối check: {current_time}*"
        
        return msg_content

    # =========================================================================
    # VÒNG LẶP CHẠY NGẦM TỰ ĐỘNG CẬP NHẬT (MỖI 1 GIỜ)
    # =========================================================================
    @tasks.loop(hours=1.0)
    async def update_leaderboard_loop(self):
        await self.bot.wait_until_ready()

        channel_id_str = database.get_setting("lb_channel_id")
        msg_id_str = database.get_setting("lb_message_id")

        if not channel_id_str or not msg_id_str:
            return

        try:
            channel = self.bot.get_channel(int(channel_id_str))
            if not channel:
                return

            # Cập nhật nội dung chữ thường
            new_text = await self.create_leaderboard_text()

            try:
                message = await channel.fetch_message(int(msg_id_str))
                await message.edit(content=new_text, embed=None) # Xóa embed cũ nếu có để đè chữ thường lên
            except discord.NotFound:
                # Nếu mất tin nhắn cũ, gửi tin nhắn thường mới
                new_msg = await channel.send(content=new_text)
                database.set_setting("lb_message_id", str(new_msg.id))
        except Exception as e:
            print(f"[Error Leaderboard Loop]: {e}")

    # =========================================================================
    # 3. LỆNH TRA CỨU NHANH BẰNG EMBED (DÀNH CHO TẤT CẢ MEMBER)
    # =========================================================================
    @commands.command(name="leaderboard", aliases=["lb", "top", "bxh"])
    async def show_leaderboard_embed(self, ctx):
        """Lệnh tra cứu bảng xếp hạng và thứ hạng của bản thân dưới dạng Embed"""
        
        # Tạo khung Embed
        embed = discord.Embed(
            title="🏮 BẢNG XẾP HẠNG EVENT TRUNG THU 🏮",
            description="Danh sách **Top 10** member ghép được nhiều **Hộp Bánh** nhất",
            color=discord.Color.from_rgb(255, 165, 0) # Màu cam nhạt lễ hội
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1260125199324549220/1524808700173357248/ezgif.com-remove-background.gif?ex=6a511843&is=6a4fc6c3&hm=efefd116305f5788a914e3900db4c5e1daaf2edc3587156570c97ebab84d395f&=&width=800&height=800") # Thay bằng icon hộp bánh nếu muốn

        # Lấy Top 10 từ DB
        top_players = database.get_top_bakers(10)
        
        if not top_players:
            embed.add_field(
                name="Trống rỗng!", 
                value="*Chưa có ai trong Server ghép được Hộp Bánh nào.*", 
                inline=False
            )
        else:
            lb_lines = []
            medal_emojis = {1: "<a:medal1:1523749987433975899>", 2: "<a:medal2:1523749990126714891>", 3: "<a:medal3:1523749987433975899>"}

            for index, (user_id, count) in enumerate(top_players, start=1):
                emoji = medal_emojis.get(index, f"`#{index}`")
                try:
                    user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    user_name = user.display_name if user else f"User ID: {user_id}"
                except:
                    user_name = f"User ID: {user_id}"

                # Bôi đậm tên nếu người trong Top 10 chính là người đang gõ lệnh
                if int(user_id) == ctx.author.id:
                    lb_lines.append(f"{emoji} **`[{user_name}]`** — **{count} Hộp** 👈 *(Bạn)*")
                else:
                    lb_lines.append(f"{emoji} **{user_name}** — `{count} Hộp`")

            embed.add_field(name="<a:arrow1:1523747492326408328> Top 10 Cao Thủ:", value="\n".join(lb_lines), inline=False)

        # --- ĐIỂM NHẤN: TRA CỨU THỨ HẠNG CỦA NGƯỜI GÕ LỆNH ---
        rank, count = database.get_user_rank_and_count(str(ctx.author.id))
        
        if rank:
            status_text = f"<a:brown_star:1523753543897710773> Bạn đang đứng hạng **#{rank}** với **`{count}` Hộp Bánh**!"
            if rank == 1:
                status_text += "\n👑 *Quá tuyệt vời! Bạn đang là người dẫn đầu Server!*"
        else:
            status_text = "<a:brown_star:1523753543897710773> Bạn hiện chưa sở hữu Hộp Bánh nào trong rương đồ!"

        embed.add_field(name="<a:arrow1:1523747492326408328> Thứ Hạng Của Bạn", value=status_text, inline=False)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)

    # =========================================================================
    # LỆNH CÀI ĐẶT KÊNH LEADERBOARD (ADMIN ONLY)
    # =========================================================================
    @commands.command(name="setleaderboard", aliases=["setlb"])
    @commands.has_permissions(administrator=True)
    async def set_leaderboard_channel(self, ctx):
        """Thiết lập kênh hiện tại làm nơi hiển thị Bảng Xếp Hạng cố định"""
        
        await ctx.send("⚙️ Đang thiết lập kênh Leaderboard, vui lòng đợi...", delete_after=3)
        
        try:
            await ctx.message.delete()
        except:
            pass

        # Tạo văn bản text thường
        leaderboard_text = await self.create_leaderboard_text()
        
        # Gửi dưới dạng nội dung (content) bình thường
        lb_message = await ctx.send(content=leaderboard_text)

        # Lưu thông tin để edit định kỳ
        database.set_setting("lb_channel_id", str(ctx.channel.id))
        database.set_setting("lb_message_id", str(lb_message.id))

        temp_msg = await ctx.send(f"✅ Đã thiết lập thành công bảng xếp hạng chữ thường tại kênh này!")
        await asyncio.sleep(5)
        try:
            await temp_msg.delete()
        except:
            pass

    @set_leaderboard_channel.error
    async def set_leaderboard_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn cần có quyền `Administrator` để thiết lập kênh Bảng Xếp Hạng!")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))

