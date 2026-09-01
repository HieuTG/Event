import discord
from discord.ext import commands
import database
import sys
import os

# Import module security_log để ghi log
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from security_log import log_admin_action
except ImportError:
    # Fallback nếu chưa load module
    def log_admin_action(*args, **kwargs): pass

# Bản đồ mã vật phẩm giống các file trước
ITEM_MAP = {
    "dauxanh": ("dau_xanh", "🟢 Đậu Xanh"),
    "dx": ("dau_xanh", "🟢 Đậu Xanh"),
    "thapcam": ("thap_cam", "🥮 Thập Cẩm"),
    "tc": ("thap_cam", "🥮 Thập Cẩm"),
    "meden": ("me_den", "⚫ Mè Đen"),
    "md": ("me_den", "⚫ Mè Đen"),
    "khoaimon": ("khoai_mon", "🟣 Khoai Môn"),
    "km": ("khoai_mon", "🟣 Khoai Môn"),
    "hatsen": ("hat_sen", "⚪ Hạt Sen"),
    "hs": ("hat_sen", "⚪ Hạt Sen"),
    "trungmuoi": ("trung_muoi", "🟡 Trứng Muối (HIẾM)"),
    "tm": ("trung_muoi", "🟡 Trứng Muối (HIẾM)"),
    "hopbanh": ("hop_banh", "🎁 Hộp Bánh Trung Thu"),
    "hb": ("hop_banh", "🎁 Hộp Bánh Trung Thu"),
    "mv": ("manh_vo", "🧩 Mảnh Bánh Vỡ")
}

class AdminManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="them", aliases=["add"])
    @commands.has_permissions(administrator=True) # Chỉ Admin mới dùng được
    async def add_item_command(self, ctx, target: discord.Member = None, item_key: str = None, amount: int = 1):
        """Cú pháp: !them @User <mã_vật_phẩm> [số_lượng]"""
        
        if target is None or item_key is None:
            embed = discord.Embed(
                title="🛠️ HƯỚNG DẪN LỆNH CẤP PHÁT VẬT PHẨM",
                description="**Cú pháp:** `ethem @Người_dùng <mã_vật_phẩm> [số_lượng]`\n\n"
                            "**Ví dụ:** `ethem @Duy tm 3` *(Cấp 3 Trứng muối cho Duy)*\n\n"
                            "**Mã vật phẩm:** `dx` (Đậu Xanh) | `tc` (Thập Cẩm) | `md` (Mè Đen) | `km` (Khoai Môn) | `hs` (Hạt Sen) | `tm` (Trứng Muối) | `hb` (Hộp Bánh)",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        if amount < 1:
            await ctx.send("❌ Số lượng thêm phải lớn hơn hoặc bằng 1!")
            return

        key = item_key.lower()
        if key not in ITEM_MAP:
            await ctx.send("❌ Mã vật phẩm không hợp lệ! Gõ `ethem` để xem danh sách mã.")
            return

        item_db, item_name = ITEM_MAP[key]

        # Gọi hàm cộng vật phẩm (truyền số dương)
        new_quantity = database.admin_modify_inventory(str(target.id), item_db, amount)

        # GHI LOG HÀNH ĐỘNG ADMIN
        log_admin_action(
            str(ctx.author.id), ctx.author.name,
            "ADD_ITEM",
            str(target.id), target.name,
            item_name, amount,
            f"Added {amount}x {item_name} to {target.name}'s inventory"
        )

        embed = discord.Embed(
            title="📥 ĐÃ THÊM VẬT PHẨM (ADMIN)",
            description=f"Admin {ctx.author.mention} đã cộng quà vào túi đồ của {target.mention}:\n\n"
                        f"➕ **Đã thêm:** `{amount}x` {item_name}\n"
                        f"🎒 **Số lượng hiện tại:** `{new_quantity}` cái",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


    @commands.command(name="tru", aliases=["take"])
    @commands.has_permissions(administrator=True) # Chỉ Admin mới dùng được
    async def remove_item_command(self, ctx, target: discord.Member = None, item_key: str = None, amount: int = 1):
        """Cú pháp: !tru @User <mã_vật_phẩm> [số_lượng]"""
        
        if target is None or item_key is None:
            embed = discord.Embed(
                title="🛠️ HƯỚNG DẪN LỆNH THU HỒI VẬT PHẨM",
                description="**Cú pháp:** `etru @Người_dùng <mã_vật_phẩm> [số_lượng]`\n\n"
                            "**Ví dụ:** `etru @Duy dx 2` *(Thu hồi 2 Đậu xanh của Duy)*\n\n"
                            "**Mã vật phẩm:** tương tự lệnh !them",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        if amount < 1:
            await ctx.send("❌ Số lượng trừ phải lớn hơn hoặc bằng 1!")
            return

        key = item_key.lower()
        if key not in ITEM_MAP:
            await ctx.send("❌ Mã vật phẩm không hợp lệ!")
            return

        item_db, item_name = ITEM_MAP[key]

        # Gọi hàm trừ vật phẩm (truyền số âm)
        new_quantity = database.admin_modify_inventory(str(target.id), item_db, -amount)

        # GHI LOG HÀNH ĐỘNG ADMIN
        log_admin_action(
            str(ctx.author.id), ctx.author.name,
            "REMOVE_ITEM",
            str(target.id), target.name,
            item_name, -amount,
            f"Removed {amount}x {item_name} from {target.name}'s inventory"
        )

        embed = discord.Embed(
            title="📤 ĐÃ THU HỒI VẬT PHẨM (ADMIN)",
            description=f"Admin {ctx.author.mention} đã tịch thu vật phẩm từ túi đồ của {target.mention}:\n\n"
                        f"➖ **Đã tịch thu:** `{amount}x` {item_name}\n"
                        f"🎒 **Số lượng còn lại:** `{new_quantity}` cái",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    # Xử lý khi người dùng không phải Admin cố tình gõ lệnh
    @add_item_command.error
    @remove_item_command.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Lệnh này chỉ dành cho **Quản trị viên (Admin)** của Server!")

async def setup(bot):
    await bot.add_cog(AdminManage(bot))