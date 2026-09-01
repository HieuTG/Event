import discord
from discord.ext import commands
import database

# Bản đồ công thức nấu bánh: mã_vị: (cột_db, số_mảnh_yêu_cầu, tên_hiển_thị)
COOK_RECIPES = {
    "dx": ("dau_xanh", 5, "<:dx_icon:1523756971738529802> Đậu Xanh"),
    "dauxanh": ("dau_xanh", 5, "🟢 Đậu Xanh"),
    "tc": ("thap_cam", 5, "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "thapcam": ("thap_cam", 5, "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "md": ("me_den", 5, "<:md_icon:1523756996858351756> Mè Đen"),
    "meden": ("me_den", 5, "<:md_icon:1523756996858351756> Mè Đen"),
    
    "km": ("khoai_mon", 10, "<:km_icon:1523756985047060734> Khoai Môn"),
    "khoaimon": ("khoai_mon", 10, "<:km_icon:1523756985047060734> Khoai Môn"),
    "hs": ("hat_sen", 10, "<:hs_icon:1523756991879839994> Hạt Sen"),
    "hatsen": ("hat_sen", 10, "<:hs_icon:1523756991879839994> Hạt Sen"),
    
    "tm": ("trung_muoi", 20, "<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)"),
    "trungmuoi": ("trung_muoi", 20, "<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)")
}

class Cook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="menu", aliases=["lobanh", "congthuc"])
    async def cook_menu(self, ctx):
        """Bảng công thức đúc bánh từ mảnh vỡ nấu cổ truyền"""
        embed = discord.Embed(
            title="📜 LÒ ĐÚC BÁNH CỔ TRUYỀN - CÔNG THỨC 📜",
            description=(
                "Nơi tái chế những <:manhvo:1523760564663222382> `Mảnh Bánh Vỡ` nhặt được khi trò chuyện "
                "thành những chiếc bánh nguyên vẹn hoàn chỉnh!\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            ),
            color=discord.Color.dark_gold()
        )
        
        embed.add_field(
            name="<:demir87:1523749993784283326> Vị Phổ Thông (Chi phí: 5 <:manhvo:1523760564663222382>)",
            value="<:dx_icon:1523756971738529802> `dx` (Đậu Xanh) | <:tc_icon:1523756962930757712> `tc` (Thập Cẩm) | <:md_icon:1523756996858351756> `md` (Mè Đen)",
            inline=False
        )
        
        embed.add_field(
            name="<:Minecraft_Gold_Ingot:1523749992437645522> Vị Thượng Hạng (Chi phí: 10 <:manhvo:1523760564663222382>)",
            value="<:km_icon:1523756985047060734> `km` (Khoai Môn) | <:hs_icon:1523756991879839994> `hs` (Hạt Sen)",
            inline=False
        )
        
        embed.add_field(
            name="<:Minecraft_diamond:1523749991212908544> Vị Hoàng Gia (Chi phí: 20 <:manhvo:1523760564663222382>)",
            value="<:tm_icon:1523756978663325706> `tm` (Trứng Muối)",
            inline=False
        )
        
        embed.set_footer(
            text="Cú pháp đúc bánh: !nau <mã_vị_bánh> (Ví dụ: !nau tm)",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)

    @commands.command(name="nau", aliases=["cook", "duc", "ducbanh"])
    async def cook_cake_command(self, ctx, item_key: str = None):
        """Tiến hành đúc bánh từ mảnh vỡ"""
        if item_key is None:
            await ctx.send("⚠️ Bạn muốn nấu vị nào? Cú pháp: `enau <mã_vị_bánh>` (Ví dụ: `enau tm`). Gõ `emenu` để xem công thức.")
            return

        key = item_key.lower().replace(" ", "")
        if key not in COOK_RECIPES:
            await ctx.send("❌ Mã vị bánh không tồn tại! Gõ `emenu` để xem danh sách mã hợp lệ.")
            return

        item_db, cost, item_name = COOK_RECIPES[key]
        user_id = str(ctx.author.id)

        # Gọi DB xử lý đúc bánh
        success = database.cook_cake_db(user_id, item_db, cost)

        if success:
            embed = discord.Embed(
                title="🔥 LÒ ĐỎ LỬA - ĐÚC BÁNH THÀNH CÔNG!",
                description=f"Chúc mừng {ctx.author.mention}! Lò đúc đã tiêu hao **`{cost}` <:manhvo:1523760564663222382>** và chế tạo thành công một chiếc **{item_name}** hoàn chỉnh!",
                color=discord.Color.brand_green()
            )
            await ctx.send(embed=embed)
        else:
            # Lấy số mảnh vỡ hiện tại của họ để báo lỗi cho chi tiết
            _, _, _, _, _, _, _, manh_vo = database.get_user_inventory(user_id)
            embed = discord.Embed(
                title="❌ THIẾU NGUYÊN LIỆU ĐÚC BÁNH",
                description=f"{ctx.author.mention}, bạn không có đủ số mảnh vỡ yêu cầu cho vị này!\n\n"
                            f"📋 **Yêu cầu:** `{cost}` <:manhvo:1523760564663222382>\n"
                            f"🧩 **Hiện có trong rương:** `{manh_vo}` <:manhvo:1523760564663222382>",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Cook(bot))