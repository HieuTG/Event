import discord
from discord.ext import commands
import database

# Bản đồ công thức đập bánh thành mảnh vỡ: mã_vị: (cột_db, số_mảnh_nhận_được, tier, tên_hiển_thị)
SMASH_RECIPES = {
    # Tier 1: Phổ Thông - 2 bánh đổi 1 mảnh vỡ
    "dx": ("dau_xanh", 1, "common", 2, "<:dx_icon:1523756971738529802> Đậu Xanh"),
    "dauxanh": ("dau_xanh", 1, "common", 2, "<:dx_icon:1523756971738529802> Đậu Xanh"),
    "tc": ("thap_cam", 1, "common", 2, "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "thapcam": ("thap_cam", 1, "common", 2, "<:tc_icon:1523756962930757712> Thập Cẩm"),
    "md": ("me_den", 1, "common", 2, "<:md_icon:1523756996858351756> Mè Đen"),
    "meden": ("me_den", 1, "common", 2, "<:md_icon:1523756996858351756> Mè Đen"),

    # Tier 2: Thượng Hạng - 1 bánh đổi 1 mảnh vỡ
    "km": ("khoai_mon", 1, "rare", 1, "<:km_icon:1523756985047060734> Khoai Môn"),
    "khoaimon": ("khoai_mon", 1, "rare", 1, "<:km_icon:1523756985047060734> Khoai Môn"),
    "hs": ("hat_sen", 1, "rare", 1, "<:hs_icon:1523756991879839994> Hạt Sen"),
    "hatsen": ("hat_sen", 1, "rare", 1, "<:hs_icon:1523756991879839994> Hạt Sen"),

    # Tier 3: Hoàng Gia - 1 bánh đổi 5 mảnh vỡ
    "tm": ("trung_muoi", 5, "legendary", 1, "<:tm_icon:1523756978663325706> Trứng Muối"),
    "trungmuoi": ("trung_muoi", 5, "legendary", 1, "<:tm_icon:1523756978663325706> Trứng Muối")
}

class SmashCake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dap", aliases=["smash", "vo", "dapdep"])
    async def smash_cake_command(self, ctx, item_key: str = None, amount: int = 1):
        """Đập bánh thành mảnh vỡ - Phổ thông: 2→1 | Thượng hạng: 1→1 | Hoàng gia: 1→5"""

        if item_key is None:
            await ctx.send("⚠️ Bạn muốn đập vị nào? Cú pháp: `edap <mã_vị> [số_lượng]` (Ví dụ: `edap tm 3`). Gõ `emenu` để xem bảng tỉ lệ đổi.")
            return

        key = item_key.lower().replace(" ", "")
        if key not in SMASH_RECIPES:
            await ctx.send("❌ Mã vị bánh không tồn tại! Gõ `emenu` để xem danh sách mã hợp lệ.")
            return

        if amount <= 0:
            await ctx.send("❌ Số lượng phải lớn hơn 0!")
            return

        item_db, shards_per_cake, tier, cost_per_transaction, item_name = SMASH_RECIPES[key]
        user_id = str(ctx.author.id)

        # Lấy inventory hiện tại
        dau_xanh, thap_cam, me_den, hat_sen, khoai_mon, trung_muoi, hop_banh, manh_vo = database.get_user_inventory(user_id)

        # Lấy số lượng bánh hiện tại của loại này
        current_items = {
            "dau_xanh": dau_xanh,
            "thap_cam": thap_cam,
            "me_den": me_den,
            "hat_sen": hat_sen,
            "khoai_mon": khoai_mon,
            "trung_muoi": trung_muoi
        }

        current_amount = current_items.get(item_db, 0)

        # Tính toán số bánh cần và mảnh vỡ nhận được
        total_cakes_needed = amount * cost_per_transaction
        total_shards_received = amount * shards_per_cake

        # Kiểm tra đủ bánh không
        if current_amount < total_cakes_needed:
            embed = discord.Embed(
                title="❌ THIẾU NGUYÊN LIỆU ĐỂ ĐẬP",
                description=f"{ctx.author.mention}, bạn không có đủ **{item_name}** để đập!\n\n"
                            f"📋 **Yêu cầu:** `{total_cakes_needed}` cái (Đập `{amount}` lần)\n"
                            f"🧺 **Hiện có:** `{current_amount}` cái",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Thực hiện đập bánh
        database.admin_modify_inventory(user_id, item_db, -total_cakes_needed)  # Trừ bánh
        database.add_item_to_inventory(user_id, "manh_vo", total_shards_received)  # Cộng mảnh vỡ

        # Chọn emoji theo tier
        tier_emoji = {
            "common": "<:demir87:1523749993784283326>",
            "rare": "<:Minecraft_Gold_Ingot:1523749992437645522>",
            "legendary": "<:Minecraft_diamond:1523749991212908544>"
        }

        tier_color = {
            "common": discord.Color.light_gray(),
            "rare": discord.Color.gold(),
            "legendary": discord.Color.purple()
        }

        # Tạo embed thông báo thành công
        embed = discord.Embed(
            title="🔨 ĐẬP BÁNH THÀNH CÔNG!",
            description=f"{tier_emoji[tier]} {ctx.author.mention} đã đập **`{total_cakes_needed}`** {item_name}!\n\n"
                        f"✨ **Nhận được:** `{total_shards_received}` <:manhvo:1523760564663222382> **Mảnh Bánh Vỡ**",
            color=tier_color[tier]
        )

        # Thêm thông tin tỉ lệ đổi
        rate_text = {
            "common": "📊 **Tỉ lệ:** 2 bánh → 1 mảnh vỡ",
            "rare": "📊 **Tỉ lệ:** 1 bánh → 1 mảnh vỡ",
            "legendary": "📊 **Tỉ lệ:** 1 bánh → 5 mảnh vỡ"
        }
        embed.add_field(name="💫 Độ Quý Hiếm", value=rate_text[tier], inline=False)

        embed.set_footer(text=f"Còn lại: {current_amount - total_cakes_needed} {item_name.split()[-1]}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SmashCake(bot))
