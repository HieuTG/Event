import discord
from discord.ext import commands

# --- 1. ĐỊNH NGHĨA THANH MENU DROPDOWN ---
class HelpDropdown(discord.ui.Select):
    def __init__(self, is_admin: bool):
        # Định nghĩa các mục lựa chọn (Options) xuất hiện trong Dropdown
        options = [
            discord.SelectOption(
                label="Luật chơi cơ bản",
                description="Xem hướng dẫn tham gia event & tỷ lệ rơi nguyên liệu.",
                emoji="📜"
            ),
            discord.SelectOption(
                label="Sự kiện Mưa Bánh",
                description="Thông tin về sự kiện rớt bánh tốc độ cao.",
                emoji="🌩️"
            ),
            discord.SelectOption(
                label="Balo & Hành trang",
                description="Cách kiểm tra túi đồ và các tài sản đang có.",
                emoji="🎒"
            ),
            discord.SelectOption(
                label="Giao thương / Trao đổi",
                description="Hướng dẫn trade bánh, giao dịch qua lại giữa các member.",
                emoji="🤝"
            ),
            discord.SelectOption(
                label="Chế tạo & Đổi thưởng",
                description="Công thức ghép bánh và hệ thống ticket đổi quà.",
                emoji="🎁"
            ),
            discord.SelectOption(
                label="Bảng xếp hạng",
                description="Cách xem BXH và thứ hạng của bạn.",
                emoji="🏆"
            ),
        ]
        
        # NẾU LÀ ADMIN: Tự động chèn thêm phân mục Tối Mật vào thanh cuộn
        if is_admin:
            options.append(
                discord.SelectOption(
                    label="Bảng lệnh Admin", 
                    description="Các lệnh điều phối sự kiện dành riêng cho Admin.", 
                    emoji="👑"
                )
            )
            
        super().__init__(
            placeholder="Chọn thông tin bạn muốn biết tại đây...", 
            min_values=1, 
            max_values=1, 
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # KHÓA TƯƠNG TÁC: Chỉ cho phép người gõ lệnh ehelp bấm điều hướng
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message(
                "❌ Bạn không thể điều khiển bảng trợ giúp của người khác! Hãy tự gõ `ehelp` nhé.", 
                ephemeral=True
            )
            return

        selection = self.values[0]
        embed = discord.Embed(color=discord.Color.from_rgb(255, 153, 0)) # Giữ tông vàng cam lồng đèn

        # --- XỬ LÝ NỘI DUNG TỪNG PHÂN MỤC ---
        if selection == "Luật chơi cơ bản":
            embed.title = "📜 LUẬT CHƠI CƠ BẢN - VUI HỘI TRĂNG RẰM"
            embed.description = (
                "> *Hãy tích cực trò chuyện lành mạnh cùng mọi người để có cơ hội nhặt nguyên liệu quý giá!*\n\n"
                "<a:brown_star:1523753543897710773> **Cơ chế nhặt quà:**\n"
                "• Khi bạn nhắn tin trên các kênh chat sự kiện, bạn có **10% cơ hội** nhận được quà ngẫu nhiên.\n"
                "• Hệ thống áp dụng thời gian hồi (**Cooldown**) là **1 phút** giữa mỗi lần nhặt bánh.\n\n"
                "<a:exc:1523747494805110814> **Tỷ lệ độ hiếm vật phẩm:**\n"
                "• <:manhvo:1523760564663222382> **Mảnh Bánh Vỡ:** `27%` *(Xui xẻo làm rơi, tích mảnh để nấu lại)*\n"
                "• <:dx_icon:1523756971738529802> **Đậu Xanh / <:tc_icon:1523756962930757712> Thập Cẩm / <:md_icon:1523756996858351756> Mè Đen:** `18%` mỗi loại (Phổ thông)\n"
                "• <:km_icon:1523756985047060734> **Khoai Môn / <:hs_icon:1523756991879839994> Hạt Sen:** `7%` mỗi loại (Thượng hạng)\n"
                "• <:tm_icon:1523756978663325706> **Trứng Muối:** `5%` (Siêu cấp quý hiếm!)\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )

        elif selection == "Sự kiện Mưa Bánh":
            embed.title = "🌩️ SỰ KIỆN ĐẶC BIỆT: MƯA BÁNH TRUNG THU"
            embed.description = (
                "Bên cạnh việc nhặt nguyên liệu từ việc chat, thỉnh thoảng Hằng Nga sẽ tạo ra một cơn mưa bánh bất ngờ!\n\n"
                "<:holiday_crate:1523749995059216494> **Cơ chế rớt hộp quà:**\n"
                "• Hộp quà rơi ngẫu nhiên tại các kênh chat. Ở chế độ bình thường, cứ **15-60 phút** sẽ có 1 hộp rơi xuống.\n"
                "• Khi sự kiện **MƯA BÁNH** kích hoạt, tốc độ rơi sẽ tăng vọt lên **1-2 phút/hộp**!\n\n"
                "🔔 **Lưu ý:**\n"
                "• Sự kiện diễn ra ngẫu nhiên và kéo dài trong 15-30 phút.\n"
                "• Mua role <..> để nhận thông báo sự kiện.\n"
                "• Hộp quà xuất hiện ra dưới dạng Nút Bấm (Button), ai nhanh tay bấm **Nhặt** trước sẽ lấy được quà.\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )
            
        elif selection == "Balo & Hành trang":
            embed.title = "🎒 BALO & HÀNH TRANG SỰ KIỆN"
            embed.description = (
                "Để kiểm tra xem bản thân đang sở hữu bao nhiêu nguyên liệu và thành phẩm, hãy sử dụng lệnh sau:\n\n"
                "<a:arrow1:1523747492326408328> **`eruong`** *(Hoặc viết tắt: `etui`, `etuido`, `einv`)*\n\n"
                "<:Question:1270398206420979862> **Thông tin hiển thị trong rương:**\n"
                "• Số lượng 6 loại nguyên liệu bánh hoàn chỉnh.\n"
                "• Số lượng <:manhvo:1523760564663222382> `Mảnh Bánh Vỡ` hiện có.\n"
                "• Số lượng <:holiday_crate:1523749995059216494> `Hộp Bánh Trung Thu` đã đóng gói thành công.\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )
            
        elif selection == "Giao thương / Trao đổi":
            embed.title = "🤝 HỆ THỐNG GIAO THƯƠNG & TRAO ĐỔI"
            embed.description = (
                "Bạn thiếu vị này nhưng thừa vị khác? Tính năng trao đổi sẽ giúp bạn đổi những bánh bị thừa với người khác để lấy những mảnh bị thiếu:\n\n"
                "<a:arrow1:1523747492326408328> **Lệnh:** `edoi @Người_Nhận`\n"
                "• *Ví dụ:* `edoi @Admin`\n\n"
                "<a:exc:1523747494805110814> **Lưu ý quan trọng:**\n"
                "• Cả 2 bên bắt buộc phải có đủ vật phẩm trong túi đồ thì lời mời mới được gửi đi.\n"
                "• <:manhvo:1523760564663222382> **Mảnh Bánh Vỡ** là vật phẩm đặc biệt, **KHÔNG THỂ** mang đi giao dịch.\n\n"
                "> <:blurple2monthboosting:1270403608114102304> **Mã viết tắt các loại bánh:**\n"
                "> `dx` (Đậu Xanh) | `tc` (Thập Cẩm) | `md` (Mè Đen)\n"
                "> `km` (Khoai Môn) | `hs` (Hạt Sen) | `tm` (Trứng Muối)"
            )
            
        elif selection == "Chế tạo & Đổi thưởng":
            embed.title = "🎁 CHẾ TẠO & ĐỔI THƯỞNG"
            embed.description = (
                "Nơi tái chế phế liệu và đổi thưởng từ hộp bánh:\n\n"
                "<a:smoker30:1523838199385030827> **1. Lò đúc từ Mảnh Bánh Vỡ:**\n"
                "• Gõ **`emenu`** để xem chi tiết bảng công thức đúc mảnh vỡ thành bánh nguyên vẹn.\n"
                "• Gõ **`enau <mã_vị>`** để bắt đầu nổi lửa đúc bánh. *(Ví dụ: `enau tm`)*\n\n"
                "<a:pinkstar:1504371609346117692> **2. Gói Hộp Bánh Trung Thu:**\n"
                "• Gõ **`eghep`** khi tích đủ bộ **6 vị bánh khác nhau**.\n"
                "• Hệ thống tiêu hao mỗi vị 1 cái để đóng gói thành **1 <:holiday_crate:1523749995059216494> Hộp Bánh Trung Thu**.\n\n"
                "🎫 **3. Hệ thống Ticket Đổi Thưởng:**\n"
                "• Tìm kênh ticket panel và nhấn nút **\"Nhận Thưởng Event\"**\n"
                "• Bot sẽ tạo ticket riêng cho bạn\n"
                "• Admin sẽ xử lý và trao quà cho bạn\n\n"
                "💰 **Tỷ giá đổi thưởng:**\n"
                "• 5 Hộp Bánh = 10.000 **VND**\n"
                "• 1 Hộp Bánh = 100k **OwO Cash**\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )

        elif selection == "Bảng xếp hạng":
            embed.title = "🏆 BẢNG XẾP HẠNG & THỐNG KÊ"
            embed.description = (
                "Theo dõi thứ hạng và so sánh với những cao thủ khác:\n\n"
                "<a:arrow1:1523747492326408328> **Xem bảng xếp hạng:**\n"
                "• Gõ **`eleaderboard`** (hoặc `elb`, `etop`, `ebxh`)\n"
                "• Hiển thị Top 10 người có nhiều Hộp Bánh nhất\n"
                "• Tự động hiển thị thứ hạng của bạn\n\n"
                "📊 **Thông tin hiển thị:**\n"
                "• Thứ hạng từ 1-10 với medal đặc biệt cho Top 3\n"
                "• Tổng số Hộp Bánh đã ghép của mỗi người\n"
                "• Vị trí và số bánh của bạn trong BXH\n\n"
                "🔄 **Cập nhật:**\n"
                "• Bảng xếp hạng tự động cập nhật mỗi 1 giờ\n"
                "• Kiểm tra kênh leaderboard để xem BXH real-time\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )

        elif selection == "Bảng lệnh Admin":
            embed.title = "👑 KHU VỰC QUẢN TRỊ - ADMIN ONLY"
            embed.description = (
                "Các lệnh điều phối sự kiện dành riêng cho Quản trị viên:\n\n"
                "⚙️ **Setup Bot (Quan trọng nhất!):**\n"
                "• **`/settings`** hoặc `esettings`: Mở menu cài đặt tổng hợp\n"
                "  └ Setup log channel, ticket, leaderboard, event, spawn channels\n"
                "  └ Giao diện thân thiện với nút bấm\n\n"
                "🎉 **Tạo Giveaway:**\n"
                "• `egiveaway <thời_gian> <mã> <số_lượng> [số_giải]`\n"
                "• Ví dụ: `egiveaway 10m tm 2 5`\n\n"
                "<:green_plus:1523840009415819344> **Quản lý vật phẩm:**\n"
                "• `ethem @User <mã> [số_lượng]` - Cộng đồ\n"
                "• `etru @User <mã> [số_lượng]` - Trừ đồ\n\n"
                "🎁 **Quản lý Spawn Hộp Quà:**\n"
                "• `espawn add <#kênh>` - Thêm kênh thả bánh\n"
                "• `espawn remove <#kênh>` - Xóa kênh thả bánh\n"
                "• `!spawn` - Xem danh sách | `espawn test` - Test thả\n\n"
                "🌩️ **Quản lý Event Mưa Bánh:**\n"
                "• `emuabanh on` - Bật event ngay (15-30p)\n"
                "• `emuabanh off` - Tắt event\n"
                "• `emuabanh status` - Xem trạng thái\n\n"
                "🎫 **Quản lý Ticket:**\n"
                "• `eticket setcategory <ID>` - Category chứa ticket\n"
                "• `eticket settranscript <#kênh>` - Kênh lưu log\n"
                "• `eticket addrole @Role` - Role duyệt thưởng\n"
                "• `eticket info` - Xem cấu hình\n\n"
                "💾 **Backup & Security:**\n"
                "• `ebackup` - Backup database thủ công\n"
                "• `elistbackups` - Xem danh sách backup\n"
                "• `ettradelogs @user` - Xem lịch sử trade\n"
                "• `echeckuser @user` - Kiểm tra hành vi đáng ngờ\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            )

        embed.set_footer(
            text=f"Mục đang xem: {selection} • Sử dụng dropdown bên dưới để chuyển trang", 
            icon_url=interaction.user.display_avatar.url
        )
        
        # Cập nhật thay thế Embed cũ mà không cần gửi tin nhắn mới
        await interaction.response.edit_message(embed=embed, view=self.view)


# --- 2. CONTAINER CHỨA DROPDOWN MENU ---
class HelpView(discord.ui.View):
    def __init__(self, is_admin: bool, ctx):
        super().__init__(timeout=90) # Menu tự hủy sau 90 giây không tương tác
        self.ctx = ctx
        self.message = None
        self.add_item(HelpDropdown(is_admin))

    async def on_timeout(self):
        # Khi hết thời gian, vô hiệu hóa thanh dropdown để tối ưu tài nguyên và tránh bug
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


# --- 3. COG LỆNH MAIN COMMAND ---
class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["huongdan", "event", "trungthu"])
    async def help_command(self, ctx):
        """Bảng hướng dẫn tương tác thông minh cho Sự kiện Trung Thu"""
        is_admin = ctx.author.guild_permissions.administrator
        
        # Giao diện Trang Chủ (Mặc định khi gõ lệnh)
        embed = discord.Embed(
            title="🏮 TRUNG THU EVENT - HƯỚNG DẪN CHƠI 🏮",
            description=(
                "Chào mừng bạn đến với sự kiện Trung Thu được tổ chức bởi Server **L A V I E**\n\n"
                "> **Hướng dẫn:** Toàn bộ cẩm nang hướng dẫn đã được tích hợp vào thanh cuộn bên dưới. "
                "Hãy click vào thanh Dropdown và chọn mục thông tin bạn muốn tìm hiểu nhé!\n\n"
                "<a:brown_star:1523753543897710773> __**Các danh mục tra cứu có sẵn:**__\n"
                "⠀⠀• 📜 **Luật chơi cơ bản:** Quy định nhặt quà & tỷ lệ rớt bánh.\n"
                "⠀⠀• 🌩️ **Sự kiện Mưa Bánh:** Hướng dẫn săn bánh tốc độ cao.\n"
                "⠀⠀• 🎒 **Balo & Hành trang:** Cách quản lý tài sản sự kiện.\n"
                "⠀⠀• 🤝 **Giao thương / Trao đổi:** Cách trade bánh cùng người chơi khác.\n"
                "⠀⠀• 🎁 **Chế tạo & Đổi thưởng:** Ghép bánh và hệ thống ticket đổi quà.\n"
                "⠀⠀• 🏆 **Bảng xếp hạng:** Xem thứ hạng và so sánh với cao thủ khác."
            ),
            color=discord.Color.from_rgb(255, 153, 0)
        )

        # Lời nhắn đặc quyền ẩn/hiện tinh tế trên Trang Chủ
        if is_admin:
            embed.description += "\n\n<a:brown_star:1523753543897710773> • 👑 **Bảng lệnh Admin:** Lệnh quản trị & setup bot\n*(Chỉ bạn có quyền Administrator mới nhìn thấy mục này trong menu)*."
            
        embed.set_footer(text="L A V I E • Menu tự động khóa sau 90s")
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            
        # Khởi tạo View, liên kết tin nhắn và gửi lên Discord
        view = HelpView(is_admin, ctx)
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))