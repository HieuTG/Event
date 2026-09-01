import discord
from discord.ext import commands
import time
import random
import asyncio

# Lưu trữ danh sách người dùng bị khóa tạm thời (Runtime Cache)
RESTRICTED_USERS = set()

# =========================================================================
# GIAO DIỆN NÚT BẤM XÁC MINH (CAPTCHA ANTI-SELFBOT)
# =========================================================================
class CaptchaVerificationView(discord.ui.View):
    def __init__(self, target_user: discord.Member, cog_instance):
        super().__init__(timeout=120) # Người dùng có 2 phút để xác minh
        self.target_user = target_user
        self.cog_instance = cog_instance
        self.message = None

        # Danh sách các lựa chọn (Gồm 1 đáp án đúng và các đáp án nhiễu)
        # Định dạng: (Label, Emoji, is_correct)
        options = [
            ("Bánh Trung Thu", "🥮", True),
            ("Chiếc Ô Tô", "🚗", False),
            ("Quả Bóng Đá", "⚽", False),
            ("Cây Kem Mát", "🍦", False)
        ]
        # Trộn ngẫu nhiên vị trí các nút bấm để Selfbot không đoán được vị trí tọa độ
        random.shuffle(options)

        # Tạo động các nút bấm
        for label, emoji, is_correct in options:
            button = discord.ui.Button(
                label=label, 
                emoji=emoji, 
                style=discord.ButtonStyle.secondary,
                custom_id=f"captcha_{label}_{is_correct}_{random.randint(100,999)}"
            )
            # Gắn sự kiện click cho nút
            button.callback = self.make_callback(is_correct)
            self.add_item(button)

    def make_callback(self, is_correct: bool):
        async def callback(interaction: discord.Interaction):
            # KHÓA TƯƠNG TÁC: Chỉ người bị phạt mới được bấm
            if interaction.user.id != self.target_user.id:
                await interaction.response.send_message("❌ Đây không phải bảng xác minh của bạn!", ephemeral=True)
                return

            if is_correct:
                # Gỡ block cho người dùng
                if self.target_user.id in RESTRICTED_USERS:
                    RESTRICTED_USERS.remove(self.target_user.id)
                
                # Reset lại lịch sử đếm tin nhắn spam
                if self.target_user.id in self.cog_instance.message_logs:
                    self.cog_instance.message_logs[self.target_user.id] = []

                self.stop()
                
                embed = discord.Embed(
                    title="<a:Checkmark:1524819406385840158> XÁC MINH THÀNH CÔNG!",
                    description=f"🎉 Chúc mừng {self.target_user.mention}, hệ thống đã mở khóa quyền nhận bánh cho bạn.\n👉 Hãy tiếp tục trò chuyện lành mạnh nhé!",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
                # Tự xóa tin nhắn thông báo thành công sau 5 giây cho sạch kênh
                await asyncio.sleep(5)
                try:
                    await self.message.delete()
                except:
                    pass
            else:
                await interaction.response.send_message("❌ Sai rồi! Hãy nhìn kỹ biểu tượng yêu cầu và thử lại.", ephemeral=True)

        return callback

    async def on_timeout(self):
        # Khi hết thời gian mà không bấm hoặc bấm sai block luôn
        for child in self.children:
            child.disabled = True
        
        try:
            embed = discord.Embed(
                title="🛑 XÁC MINH THẤT BẠI",
                description=f"⚡ {self.target_user.mention} đã hết thời gian xác minh danh tính.\n🔒 Bạn vẫn sẽ bị **KHÓA KHẢ NĂNG NHẬN BÁNH** cho đến khi tự gõ lệnh `exacminh` để làm lại.",
                color=discord.Color.red()
            )
            await self.message.edit(embed=embed, view=None)
        except:
            pass


# =========================================================================
# COG CHÍNH THỨC: THEO DÕI HÀNH VI & XỬ LÝ SPAM
# =========================================================================
class AntiSpamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cấu trúc: { user_id: [timestamp1, timestamp2, ...] }
        self.message_logs = {} 
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Không quét Bot và không quét tin nhắn trong DM lệnh ẩn
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        now = time.time()

        # NẾU USER ĐANG BỊ KHÓA: Bỏ qua hoàn toàn, không tính toán gì thêm
        if user_id in RESTRICTED_USERS:
            return

        # Ghi nhận lịch sử tin nhắn chat
        if user_id not in self.message_logs:
            self.message_logs[user_id] = []
        self.message_logs[user_id].append(now)

        # LỌC CỬA SỔ TRƯỢT: Chỉ giữ lại các tin nhắn trong vòng 5 phút đổ lại (300 giây)
        self.message_logs[user_id] = [t for t in self.message_logs[user_id] if now - t < 300]

        # PHÁT HIỆN BẤT THƯỜNG: Đạt ngưỡng 100 tin nhắn trong vòng 5 phút
        if len(self.message_logs[user_id]) >= 100:
            # Lập tức đưa vào danh sách đen đóng băng nhận quà
            RESTRICTED_USERS.add(user_id)
            
            # Gửi tin nhắn bắt xác minh danh tính công khai
            await self.send_verification(message.channel, message.author)

    async def send_verification(self, channel, member):
        embed = discord.Embed(
            title="🚨 CẢNH BÁO: PHÁT HIỆN HÀNH VI BẤT THƯỜNG! 🚨",
            description=(
                f"⚠️ Hệ thống ghi nhận tài khoản {member.mention} có tần suất gửi tin nhắn quá nhanh.\n\n"
                f"🔒 **Hình phạt:** Bạn tạm thời **không thể nhận bánh** khi chat.\n"
                f"👉 **Mở khóa:** Hãy click vào nút có biểu tượng **Bánh Trung Thu (🥮)** dưới đây để chứng minh bạn không phải Selfbot/Máy gửi tự động!"
            ),
            color=discord.Color.from_rgb(255, 69, 0)
        )
        embed.set_footer(text="Thời gian xác minh là 2 phút trước khi bảng hủy bỏ.")
        
        view = CaptchaVerificationView(member, self)
        msg = await channel.send(content=member.mention, embed=embed, view=view)
        view.message = msg

    # =========================================================================
    # LỆNH ĐỂ MEMBER TỰ LẤY LẠI BẢNG XÁC MINH NẾU LỠ LÀM MẤT TIN NHẮN CŨ
    # =========================================================================
    @commands.command(name="xacminh")
    async def manual_verify(self, ctx):
        """Lấy lại bảng captcha nếu đang bị khóa nhận bánh"""
        if ctx.author.id not in RESTRICTED_USERS:
            await ctx.send(f"❌ {ctx.author.mention}, tài khoản của bạn hoàn toàn bình thường, không cần xác minh!", delete_after=10)
            return
        
        await self.send_verification(ctx.channel, ctx.author)

    # =========================================================================
    # CÁC LỆNH ADMIN ĐỂ CHECK HỆ THỐNG / QUẢN LÝ KHẨN CẤP
    # =========================================================================
    @commands.group(name="anticheat", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def anticheat_group(self, ctx):
        await ctx.send("👉 Dùng: `eanticheat list` | `eanticheat unblock @User` | `eanticheat testspam`")

    @anticheat_group.command(name="list")
    @commands.has_permissions(administrator=True)
    async def anticheat_list(self, ctx):
        if not RESTRICTED_USERS:
            await ctx.send("✅ Hiện tại không có user nào bị khóa diện nghi vấn spam.")
            return
        mentions = [f"<@{uid}>" for uid in RESTRICTED_USERS]
        await ctx.send(f"🔒 **Danh sách đang bị chặn farm bánh ({len(RESTRICTED_USERS)}):**\n" + ", ".join(mentions))

    @anticheat_group.command(name="unblock")
    @commands.has_permissions(administrator=True)
    async def anticheat_unblock(self, ctx, member: discord.Member):
        if member.id in RESTRICTED_USERS:
            RESTRICTED_USERS.remove(member.id)
            if member.id in self.message_logs:
                self.message_logs[member.id] = []
            await ctx.send(f"🔓 Đã giải oan và mở khóa thủ công cho {member.mention}!")
        else:
            await ctx.send("❌ Người này không nằm trong danh sách chặn.")

    @anticheat_group.command(name="testspam")
    @commands.has_permissions(administrator=True)
    async def anticheat_testspam(self, ctx):
        """Ép hệ thống kích hoạt bảng xác minh lên chính Admin để test xem hoạt động không"""
        await ctx.send("⚙️ Đang kích hoạt Captcha Test lên bạn...", delete_after=3)
        RESTRICTED_USERS.add(ctx.author.id)
        await self.send_verification(ctx.channel, ctx.author)

async def setup(bot):
    await bot.add_cog(AntiSpamCog(bot))