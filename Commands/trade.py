import discord
from discord.ext import commands
import database
import sys
import os

# Import module security_log để ghi log
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from security_log import log_trade, log_suspicious_activity
except ImportError:
    # Fallback nếu chưa load module
    def log_trade(*args, **kwargs): pass
    def log_suspicious_activity(*args, **kwargs): pass

# Bản đồ tra cứu mã bánh (Không bao gồm mảnh vỡ vì mảnh vỡ không cho trade)
ITEM_MAP = {
    "dx": ("dau_xanh", "<:dx_icon:1523756971738529802> Đậu Xanh"), "dauxanh": ("dau_xanh", "🟢 Đậu Xanh"),
    "tc": ("thap_cam", "<:tc_icon:1523756971738529802> Thập Cẩm"), "thapcam": ("thap_cam", "🥮 Thập Cẩm"),
    "md": ("me_den", "<:md_icon:1523756971738529802> Mè Đen"), "meden": ("me_den", "⚫ Mè Đen"),
    "km": ("khoai_mon", "<:km_icon:1523756971738529802> Khoai Môn"), "khoaimon": ("khoai_mon", "🟣 Khoai Môn"),
    "hs": ("hat_sen", "<:hs_icon:1523756971738529802> Hạt Sen"), "hatsen": ("hat_sen", "⚪ Hạt Sen"),
    "tm": ("trung_muoi", "<:tm_icon:1523756971738529802> Trứng Muối"), "trungmuoi": ("trung_muoi", "🟡 Trứng Muối")
}

# =========================================================================
# 1. VIEW KHỞI ĐẦU CHỨA NÚT MỞ FORM GIAO DỊCH
# =========================================================================
class TradeViewInit(discord.ui.View):
    def __init__(self, ctx, target):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.target = target
        self.message = None

    @discord.ui.button(label="📝 Mở Form Giao Dịch", style=discord.ButtonStyle.green)
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chặn không cho người lạ bấm vào nút mở form của chủ lệnh
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Chỉ người khởi xướng lệnh trade mới được quyền điền form!", ephemeral=True)
            return
        
        # Gọi hộp thoại Form điền thông tin lên màn hình người dùng
        modal = TradeModal(self.ctx, self.target, self)
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⏳ Đã hết thời gian phản hồi mở form trade (60s).", view=self)
            except:
                pass

# =========================================================================
# 2. MODAL DIALOG - FORM ĐIỀN THÔNG TIN CHI TIẾT
# =========================================================================
class TradeModal(discord.ui.Modal):
    def __init__(self, ctx, target, init_view):
        super().__init__(title="THÔNG TIN TRAO ĐỔI VẬT PHẨM")
        self.ctx = ctx
        self.target = target
        self.init_view = init_view

        # Khai báo các ô nhập liệu đầu vào
        self.item_give_input = discord.ui.TextInput(label="Mã vật phẩm BẠN ĐƯA (dx, tc, md...)", placeholder="Ví dụ: tm", required=True, max_length=10)
        self.amount_give_input = discord.ui.TextInput(label="Số lượng BẠN ĐƯA", placeholder="Ví dụ: 1", required=True, max_length=5)
        self.item_get_input = discord.ui.TextInput(label="Mã vật phẩm BẠN MUỐN LẤY", placeholder="Ví dụ: dx", required=True, max_length=10)
        self.amount_get_input = discord.ui.TextInput(label="Số lượng BẠN MUỐN LẤY", placeholder="Ví dụ: 5", required=True, max_length=5)

        self.add_item(self.item_give_input)
        self.add_item(self.amount_give_input)
        self.add_item(self.item_get_input)
        self.add_item(self.amount_get_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Dừng bộ đếm thời gian của View khởi đầu lại
        self.init_view.stop()

        key_give = self.item_give_input.value.lower().strip()
        key_get = self.item_get_input.value.lower().strip()

        # Kiểm tra tính hợp lệ của mã bánh
        if key_give not in ITEM_MAP or key_get not in ITEM_MAP:
            await interaction.response.send_message("❌ Mã vật phẩm không hợp lệ! Vui lòng gõ đúng mã (dx, tc, md, km, hs, tm).", ephemeral=True)
            return

        # Kiểm tra tính hợp lệ của số lượng nhập vào
        try:
            amt_give = int(self.amount_give_input.value.strip())
            amt_get = int(self.amount_get_input.value.strip())
            if amt_give <= 0 or amt_get <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Số lượng nhập vào phải là một số nguyên dương (lớn hơn 0)!", ephemeral=True)
            return

        item_give_db, item_give_name = ITEM_MAP[key_give]
        item_get_db, item_get_name = ITEM_MAP[key_get]

        # Kiểm tra kiểm toán rương đồ tức thì của hai bên
        inv_a = database.get_user_inventory(str(self.ctx.author.id))
        inv_b = database.get_user_inventory(str(self.target.id))
        
        # Map số thứ tự cột trong DB để đối soát
        db_indices = {"dau_xanh":0, "thap_cam":1, "me_den":2, "hat_sen":3, "khoai_mon":4, "trung_muoi":5, "hop_banh":6}
        
        if inv_a[db_indices[item_give_db]] < amt_give:
            await interaction.response.send_message(f"❌ Bạn không đủ số lượng `{amt_give}x` {item_give_name} trong balo để giao dịch!", ephemeral=True)
            return
            
        if inv_b[db_indices[item_get_db]] < amt_get:
            await interaction.response.send_message(f"❌ Đối phương ({self.target.display_name}) không sở hữu đủ `{amt_get}x` {item_get_name} để đổi với bạn!", ephemeral=True)
            return

        # Mọi thứ hoàn hảo -> Kích hoạt tăng 1 lượt sử dụng lệnh trong ngày của chủ lệnh
        database.increment_trade_limit(str(self.ctx.author.id))

        # Cải tiến thẩm mỹ: Chuyển đổi tin nhắn cũ thành Bảng Đề Xuất kèm nút Phán Quyết cho đối phương
        embed = discord.Embed(
            title="🤝 ĐỀ XUẤT TRAO ĐỔI",
            description=f"{self.ctx.author.mention} gửi một đề xuất trao đổi vật phẩm đến {self.target.mention}.\n"
                        f"> *Vui lòng kiểm tra số lượng, sản phẩm trước khi đưa ra quyết định!*",
            color=discord.Color.teal()
        )
        embed.add_field(name="📤 Bên đề xuất đưa:", value=f"**`{amt_give}x`** {item_give_name}", inline=True)
        embed.add_field(name="📥 Muốn nhận lại:", value=f"**`{amt_get}x`** {item_get_name}", inline=True)
        embed.set_footer(text=f"Quyền quyết định thuộc về {self.target.display_name} • Hết hạn sau 2 phút")

        decision_view = TradeViewDecision(self.ctx, self.target, item_give_db, item_give_name, amt_give, item_get_db, item_get_name, amt_get)
        
        # SỬA LẠI TIN NHẮN GỐC: Xóa nút mở form cũ đi, nạp cụm nút Đồng ý / Từ chối vào
        await interaction.response.edit_message(content=None, embed=embed, view=decision_view)
        decision_view.message = await interaction.original_response()


# =========================================================================
# 3. VIEW PHÁN QUYẾT (ĐỒNG Ý / TỪ CHỐI) - DÀNH RIÊNG CHO ĐỐI PHƯƠNG
# =========================================================================
class TradeViewDecision(discord.ui.View):
    def __init__(self, ctx, target, item_give_db, item_give_name, amt_give, item_get_db, item_get_name, amt_get):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.target = target
        self.item_give_db = item_give_db
        self.item_give_name = item_give_name
        self.amt_give = amt_give
        self.item_get_db = item_get_db
        self.item_get_name = item_get_name
        self.amt_get = amt_get
        self.message = None

    @discord.ui.button(label="✅ Đồng Ý Đổi", style=discord.ButtonStyle.green)
    async def accept_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chỉ người được tag mời trade mới có quyền quyết định kết quả
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ Chỉ đối phương được mời giao dịch mới bấm được nút này!", ephemeral=True)
            return

        self.stop()
        
        # Thực thi giao dịch chênh lệch số lượng vào cơ sở dữ liệu
        success = database.execute_flexible_trade(
            str(self.ctx.author.id), self.item_give_db, self.amt_give,
            str(self.target.id), self.item_get_db, self.amt_get
        )

        for child in self.children:
            child.disabled = True

        if success:
            # GHI LOG TRADE THÀNH CÔNG
            log_trade(
                str(self.ctx.author.id), self.ctx.author.name,
                self.item_give_db, self.amt_give,
                str(self.target.id), self.target.name,
                self.item_get_db, self.amt_get,
                success=True
            )

            embed = discord.Embed(
                title="🎉 TRAO ĐỔI THÀNH CÔNG! 🎉",
                description=f"Trao đổi giữa {self.ctx.author.mention} và {self.target.mention} đã được chấp thuận!\n\n"
                            f"• {self.ctx.author.mention} nhận về: `{self.amt_get}x` {self.item_get_name}\n"
                            f"• {self.target.mention} nhận về: `{self.amt_give}x` {self.item_give_name}\n\n"
                            f"✅ *Tài sản đã tự động hoán đổi trực tiếp trong `eruong` của hai bên!*",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # GHI LOG TRADE THẤT BẠI
            log_trade(
                str(self.ctx.author.id), self.ctx.author.name,
                self.item_give_db, self.amt_give,
                str(self.target.id), self.target.name,
                self.item_get_db, self.amt_get,
                success=False
            )

            embed = discord.Embed(
                title="❌ GIAO DỊCH THẤT BẠI",
                description=f"Giao dịch tự động hủy do tại thời điểm bấm nút, một trong hai bên đã tiêu hao vật phẩm hoặc không còn đủ số lượng bánh như thỏa thuận trong form!",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Từ Chối", style=discord.ButtonStyle.red)
    async def deny_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ Chỉ đối phương được mời giao dịch mới bấm được nút này!", ephemeral=True)
            return

        self.stop()
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="🚫 GIAO DỊCH BỊ TỪ CHỐI",
            description=f"{self.target.mention} đã từ chối đề nghị trao đổi từ {self.ctx.author.mention}.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                embed = discord.Embed(
                    title="⏳ GIAO DỊCH HẾT HẠN",
                    description="Yêu cầu giao dịch đã tự động hủy bỏ do đối phương không phản hồi sau 2 phút.",
                    color=discord.Color.dark_gray()
                )
                await self.message.edit(embed=embed, view=self)
            except:
                pass


# =========================================================================
# 4. CHÍNH COG LỆNH KHỞI CHẠY LỆNH TRADE
# =========================================================================
class TradeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trade", aliases=["doi", "traodoi"])
    async def trade_command(self, ctx, target: discord.Member = None):
        """Khởi động quy trình giao dịch bằng Form điền thông tin thông minh"""
        if target is None:
            await ctx.send("⚠️ Bạn muốn giao dịch với ai? Lệnh: `etrade @Tên_Người_Dùng`")
            return

        if target.id == ctx.author.id:
            await ctx.send("❌ Bạn không thể tự giao dịch với chính bản thân mình!")
            return

        if target.bot:
            await ctx.send("❌ Bạn không thể giao dịch với các thực thể AI/Bot hệ thống!")
            return

        # KIỂM TRA GIỚI HẠN: Chỉ được dùng tối đa 2 lệnh trade trong 1 ngày
        if not database.check_trade_limit(str(ctx.author.id)):
            await ctx.send(f"❌ {ctx.author.mention}, bạn đã dùng hết giới hạn **2 lệnh trade** của hôm nay rồi! Hãy quay lại vào ngày mai nhé.")
            return

        # Tạo tin nhắn mời gọi kèm nút mở form
        embed = discord.Embed(
            title="🏮 HỘI QUÁN GIAO THƯƠNG TRUNG THU 🏮",
            description=f"{ctx.author.mention} muốn đề xuất trao đổi bánh với {target.mention}!\n\n"
                        f"<:blue_point:1270403608114102304> **Bước 1:** {ctx.author.mention} bấm nút **📝 Mở Form Giao Dịch** ở dưới.\n"
                        f"<:blue_point:1270403608114102304> **Bước 2:** Điền đầy đủ mã bánh, số lượng đưa và nhận theo ý muốn.\n"
                        f"<:blue_point:1270403608114102304> **Bước 3:** Bấm gửi form. Đợi đối phương xác nhận.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Nút bấm mở form chỉ hoạt động với người gõ lệnh.")
        
        view = TradeViewInit(ctx, target)
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(TradeCommand(bot))