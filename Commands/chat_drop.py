import discord
from discord.ext import commands
import random
import time
import database

# 🛑 IMPORT DANH SÁCH ĐEN TỪ FILE ANTI-CHEAT
# (Đảm bảo file anti_cheat.py nằm cùng thư mục với file này)
try:
    from .anti_cheat import RESTRICTED_USERS
except ImportError:
    from anti_cheat import RESTRICTED_USERS

class ChatDrop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} 
        self.COOLDOWN_TIME = 60 # 1 phút Cooldown (60 giây)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bỏ qua bot và tin nhắn DM riêng tư
        if message.author.bot or message.guild is None:
            return

        # 🛑 CHẶN ANTI-CHEAT: NẾU USER NẰM TRONG DANH SÁCH SPAM -> BỎ QUA KHÔNG CHO RỚT BÁNH
        if message.author.id in RESTRICTED_USERS:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        user_id = str(message.author.id)
        current_time = time.time()

        # Kiểm tra Cooldown
        if user_id in self.cooldowns:
            time_passed = current_time - self.cooldowns[user_id]
            if time_passed < self.COOLDOWN_TIME:
                return 

        if random.random() > 0.1:  # 10% cơ hội rớt bánh
            return 

        rand_item = random.choices(
            population=["dau_xanh", "thap_cam", "me_den", "khoai_mon", "hat_sen", "trung_muoi", "manh_vo"],
            weights=[18, 18, 18, 7, 7, 5, 27],
            k=1
        )[0]

        database.add_item_to_inventory(user_id, rand_item, 1)
        self.cooldowns[user_id] = current_time

        if rand_item == "manh_vo":
            # Tin nhắn hài hước khi rớt trúng mảnh vỡ
            embed = discord.Embed(
                description=f"<a:cross:1524034523048837190> **Xui quá!** {message.author.mention} vừa tìm thấy một chiếc bánh nhưng xui quá, trượt tay làm rơi vỡ mất rồi! Nhận **<:manhvo:1523760564663222382> Mảnh Bánh Vỡ**\n*(Đừng buồn, gom đủ mảnh mang vào lò `emenu` nấu lại nhé)*",
                color=discord.Color.from_rgb(255, 85, 0) # Màu cam đỏ tiếc nuối
            )
        else:
            # Tin nhắn chúc mừng khi nhận được nguyên liệu nguyên vẹn
            item_display = {
                "dau_xanh": "<:dx_icon:1523756971738529802> Đậu Xanh",
                "thap_cam": "<:tc_icon:1523756962930757712> Thập Cẩm",
                "me_den": "<:md_icon:1523756996858351756> Mè Đen",
                "khoai_mon": "<:km_icon:1523756985047060734> Khoai Môn",
                "hat_sen": "<:hs_icon:1523756991879839994> Hạt Sen",
                "trung_muoi": "<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)"
            }
            embed = discord.Embed(
                description=f"<a:lucky:1524034548709724262> **May Mắn!** {message.author.mention} vừa nhặt được nguyên liệu **{item_display[rand_item]}**!",
                color=discord.Color.gold()
            )

        await message.channel.send(embed=embed, delete_after=15)

async def setup(bot):
    await bot.add_cog(ChatDrop(bot))