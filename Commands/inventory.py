import discord
from discord.ext import commands
import database
import time

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}  # Dictionary để lưu cooldown cho mỗi user

    @commands.command(name="ruong", aliases=["tui", "tuido", "bag", "inv"])
    @commands.cooldown(1, 5, commands.BucketType.user)  # 1 lần mỗi 5 giây cho mỗi user
    async def view_inventory(self, ctx):
        user_id = str(ctx.author.id)
        
        # 1. Nhận đủ 8 tham số vật phẩm hiện có từ Database
        dau_xanh, thap_cam, me_den, hat_sen, khoai_mon, trung_muoi, hop_banh, manh_vo = database.get_user_inventory(user_id)
        
        # 2. Lấy thêm thống kê tổng số hộp bánh đã từng ghép (từ bảng thống kê/leaderboard)
        # Nếu chưa từng ghép hoặc hàm trả về None, mặc định là 0
        total_crafted = database.get_total_crafted_boxes(user_id)
        
        embed = discord.Embed(
            title="<:rare_crate:1523749996695130262> TÚI ĐỒ TRUNG THU",
            description=f"Thành viên: {ctx.author.mention}\nTích lũy nguyên liệu để ghép bánh, hoặc nấu mảnh vỡ thành vị mong muốn!",
            color=discord.Color.orange()
        )
        
        common_items = (
            f"⠀⠀<:dx_icon:1523756971738529802> **Đậu Xanh:** `{dau_xanh}` cái\n"
            f"⠀⠀<:tc_icon:1523756962930757712> **Thập Cẩm:** `{thap_cam}` cái\n"
            f"⠀⠀<:md_icon:1523756996858351756> **Mè Đen:** `{me_den}` cái"
        )
        embed.add_field(name="<a:brown_star:1523753543897710773> __Nguyên Liệu Phổ Thông__ <:demir87:1523749993784283326>", value=common_items, inline=False)
        
        rare_items = (
            f"⠀⠀<:km_icon:1523756985047060734> **Khoai Môn:** `{khoai_mon}` cái\n"
            f"⠀⠀<:hs_icon:1523756991879839994> **Hạt Sen:** `{hat_sen}` cái\n"
            f"⠀⠀<:tm_icon:1523756978663325706> **Trứng Muối (HIẾM):** `{trung_muoi}` cái"
        )
        embed.add_field(name="<a:brown_star:1523753543897710773> __Nguyên Liệu Thượng Hạng__ <:Minecraft_Gold_Ingot:1523749992437645522>", value=rare_items, inline=False)
        
        # Thêm hiển thị cho Mảnh Vỡ Bánh
        embed.add_field(
            name="<a:brown_star:1523753543897710773> __Nguyên Liệu Đặc Biệt (Không thể Trade)__",
            value=f"⠀⠀<:manhvo:1523760564663222382> **Mảnh Bánh Vỡ:** `{manh_vo}` mảnh *(`emenu` để xem công thức nấu)*",
            inline=False
        )
        
        # --- ĐIỂM THAY ĐỔI: HIỆN SỐ BÁNH HIỆN TẠI KÈM TỔNG SỐ ĐÃ GHÉP ---
        thanh_pham_value = (
            f"⠀⠀<:holiday_crate:1523749995059216494> **Hộp Bánh Trung Thu:** `{hop_banh}` hộp *(Đã ghép: `{total_crafted}` hộp)*\n"
            f"⠀⠀*👉 Dùng lệnh `eghep` để chế tạo hộp!*"
        )
        embed.add_field(
            name="<a:arrow1:1523747492326408328>  __Thành Phẩm__", 
            value=thanh_pham_value, 
            inline=False
        )
        
        embed.set_footer(text=f"Túi đồ của {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @view_inventory.error
    async def inventory_error(self, ctx, error):
        """Xử lý lỗi cooldown"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ {ctx.author.mention}, bạn đang xem túi đồ quá nhanh! Vui lòng đợi **{error.retry_after:.1f}s** nữa.", delete_after=5)

async def setup(bot):
    await bot.add_cog(Inventory(bot))