import discord
from discord.ext import commands
import asyncio
import random
import time
import database

# Bản đồ vật phẩm hợp lệ để Admin phát quà (có thêm Hộp Bánh Trung Thu)
ITEM_MAP = {
    "dauxanh": ("dau_xanh", "<:dx_icon:1523756971738529802> Đậu Xanh"),
    "dx": ("dau_xanh", "<:dx_icon:1523756971738529802> Đậu Xanh"),
    "thapcam": ("thap_cam", "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "tc": ("thap_cam", "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "meden": ("me_den", "<:md_icon:1523756996858351756> Mè Đen"),
    "md": ("me_den", "<:md_icon:1523756996858351756> Mè Đen"),
    "khoaimon": ("khoai_mon", "<:km_icon:1523756985047060734> Khoai Môn"),
    "km": ("khoai_mon", "<:km_icon:1523756985047060734> Khoai Môn"),
    "hatsen": ("hat_sen", "<:hs_icon:1523756991879839994> Hạt Sen"),
    "hs": ("hat_sen", "<:hs_icon:1523756991879839994> Hạt Sen"),
    "trungmuoi": ("trung_muoi", "<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)"),
    "tm": ("trung_muoi", "<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)"),
    "hopbanh": ("hop_banh", "<:hb_icon:1523756981444024832> Hộp Bánh Trung Thu"),
    "hb": ("hop_banh", "<:hb_icon:1523756981444024832> Hộp Bánh Trung Thu")
}

def parse_duration(duration_str: str):
    """Chuyển đổi chuỗi thời gian (ví dụ: 30s, 5m, 1h) sang giây."""
    unit = duration_str[-1].lower()
    if unit == 's':
        return int(duration_str[:-1])
    elif unit == 'm':
        return int(duration_str[:-1]) * 60
    elif unit == 'h':
        return int(duration_str[:-1]) * 3600
    elif unit == 'd':
        return int(duration_str[:-1]) * 86400
    else:
        return int(duration_str)  # Mặc định hiểu là giây nếu không ghi đơn vị

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participants = set()  # Sử dụng Set để tránh một người tham gia nhiều lần

    @discord.ui.button(label="Tham Gia Giveaway (0)", style=discord.ButtonStyle.primary, emoji="🎉")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in self.participants:
            await interaction.response.send_message("⚠️ Bạn đã tham gia giveaway này rồi! Chúc bạn may mắn nhé!", ephemeral=True)
            return

        # Thêm người chơi vào danh sách
        self.participants.add(user_id)
        
        # Cập nhật số lượng hiển thị trên nút bấm
        button.label = f"Tham Gia Giveaway ({len(self.participants)})"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ Bạn đã đăng ký tham gia Giveaway thành công!", ephemeral=True)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="giveaway", aliases=["ga", "phatqua"])
    @commands.has_permissions(administrator=True)  # CHỈ ADMIN MỚI ĐƯỢC DÙNG LỆNH NÀY
    async def start_giveaway(self, ctx, duration: str = None, item_key: str = None, amount: int = 1, winners_count: int = 1):
        """
        Cú pháp: egiveaway <thời_gian> <mã_vật_phẩm> <số_lượng_mỗi_người> [số_người_thắng]
        Ví dụ: egiveaway 5m tm 2 3  -> (Phát 2 Trứng Muối cho 3 người thắng trong 5 phút)
        """
        if duration is None or item_key is None:
            embed = discord.Embed(
                title="⚠️ HƯỚNG DẪN TẠO GIVEAWAY TRUNG THU",
                description="**Cú pháp:** `egiveaway <thời_gian> <mã_vật_phẩm> <số_lượng> [số_người_thắng]`\n\n"
                            "**Ví dụ:** `egiveaway 10m tm 1 5` *(Tạo GA kéo dài 10 phút, phát 1 Trứng Muối cho 5 bạn may mắn nhất)*\n\n"
                            "**Đơn vị thời gian:** `s` (giây), `m` (phút), `h` (giờ)\n\n"
                            "**Mã vật phẩm:**\n"
                            "`dx` (Đậu Xanh) | `tc` (Thập Cẩm) | `md` (Mè Đen)\n"
                            "`km` (Khoai Môn) | `hs` (Hạt Sen) | `tm` (Trứng Muối) | `hb` (Hộp Bánh)",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        try:
            seconds = parse_duration(duration)
        except ValueError:
            await ctx.send("❌ Định dạng thời gian không hợp lệ! Vui lòng dùng `30s`, `5m` hoặc `1h`.")
            return

        key = item_key.lower()
        if key not in ITEM_MAP:
            await ctx.send("❌ Mã vật phẩm không hợp lệ! Gõ `!giveaway` để xem danh sách mã.")
            return

        item_db, item_name = ITEM_MAP[key]
        end_time = int(time.time()) + seconds

        # Tạo Embed thông báo Giveaway
        embed = discord.Embed(
            title="<a:tada_left:1523846290927124490>  GIVEAWAY TRUNG THU ĐẶC BIỆT! <a:tada_right:1523846292105724035>",
            description=f"Admin {ctx.author.mention} đang phát quà cho mọi người!\n\n"
                        f"<:Gift:1270398858576265226> **Phần thưởng:** `{amount}x` {item_name}\n"
                        f"🏆 **Số người thắng:** `{winners_count}` người\n"
                        f"<a:clock:1523847638280306819> **Kết thúc vào:** <t:{end_time}:R> (<t:{end_time}:T>)\n\n"
                        f"<a:arrow1:1523747492326408328> *Bấm vào nút **🎉 Tham Gia** bên dưới để thử vận may!*",
            color=discord.Color.from_rgb(255, 105, 180)  # Màu hồng rực rỡ
        )
        embed.set_footer(text="L A V I E • Sự kiện Trung Thu", icon_url=ctx.guild.icon.url)

        view = GiveawayView(timeout=seconds)
        ga_message = await ctx.send(embed=embed, view=view)

        # Chờ đợi cho đến khi hết giờ
        await asyncio.sleep(seconds)

        # Disable nút bấm khi hết giờ
        for child in view.children:
            child.disabled = True
            child.label = f"Đã Kết Thúc ({len(view.participants)} người tham gia)"

        # XỬ LÝ KẾT QUẢ
        participants = list(view.participants)
        
        if len(participants) == 0:
            embed.description += "\n\n❌ **Kết quả:** Không có ai tham gia giveaway này!"
            embed.color = discord.Color.dark_gray()
            await ga_message.edit(embed=embed, view=view)
            await ctx.send("❌ Giveaway đã kết thúc nhưng không có ai tham gia!")
            return

        # Chọn lọc người thắng (nếu người tham gia ít hơn số giải thì lấy tất cả)
        actual_winners_count = min(winners_count, len(participants))
        winners = random.sample(participants, actual_winners_count)

        # Cộng quà trực tiếp vào Database cho những người thắng
        winner_mentions = []
        for winner_id in winners:
            database.add_item_to_inventory(str(winner_id), item_db, amount)
            winner_mentions.append(f"<@{winner_id}>")

        winners_string = ", ".join(winner_mentions)
        
        # Cập nhật lời nhắn trên Embed gốc
        embed.title = "🎊 GIVEAWAY ĐÃ KẾT THÚC! 🎊"
        embed.description = f"<:Gift:1270398858576265226> **Phần thưởng:** `{amount}` {item_name}\n" \
                            f"🏆 **Người chiến thắng:** {winners_string}\n\n" \
                            f"<:green_plus:1523840009415819344> *Vật phẩm đã được tự động thêm vào `eruong` của người thắng!*"
        embed.color = discord.Color.gold()
        await ga_message.edit(embed=embed, view=view)

        # Gửi tin nhắn chúc mừng tag tên người thắng
        congratulations_msg = f"<a:tada_left:1523846290927124490> Chúc mừng {winners_string} đã thắng Giveaway! Bạn vừa nhận được **`{amount}x` {item_name}** vào túi đồ (`eruong`)!"
        await ctx.send(congratulations_msg)

    @start_giveaway.error
    async def giveaway_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn không có quyền Admin để tổ chức Giveaway!")

async def setup(bot):
    await bot.add_cog(Giveaway(bot))