import discord
from discord.ext import commands
from discord import app_commands
import database

class SettingsView(discord.ui.View):
    """View chính cho settings menu"""
    def __init__(self, ctx):
        super().__init__(timeout=300)  # 5 phút timeout
        self.ctx = ctx
        self.message = None

    async def update_embed(self, interaction=None):
        """Cập nhật embed hiển thị cài đặt hiện tại"""
        # Lấy thông tin cài đặt hiện tại
        log_channel_id = database.get_setting("log_channel_id")
        spawn_channels = database.get_all_spawn_channels()
        ticket_channel_id = database.get_setting("ticket_channel_id")
        lb_channel_id = database.get_setting("lb_channel_id")
        event_channel_id = database.get_setting("event_channel_id")
        event_role_id = database.get_setting("event_role_id")

        embed = discord.Embed(
            title="⚙️ CÀI ĐẶT BOT TRUNG THU",
            description="Quản lý các thiết lập quan trọng của bot cho server này.\n"
                       "*Chỉ Admin mới có thể thay đổi cài đặt.*",
            color=discord.Color.blue()
        )

        # Hiển thị Log Channel
        if log_channel_id:
            log_channel = self.ctx.guild.get_channel(int(log_channel_id))
            log_display = log_channel.mention if log_channel else f"~~<#{log_channel_id}>~~ *(Đã xóa)*"
        else:
            log_display = "❌ *Chưa thiết lập*"

        embed.add_field(
            name="📋 Kênh Ghi Log (Admin)",
            value=f"{log_display}\n"
                  f"*Kênh nhận thông báo về: backup, ticket, admin logs*",
            inline=False
        )

        # Hiển thị Ticket Channel
        if ticket_channel_id:
            ticket_channel = self.ctx.guild.get_channel(int(ticket_channel_id))
            ticket_display = ticket_channel.mention if ticket_channel else f"~~<#{ticket_channel_id}>~~ *(Đã xóa)*"
        else:
            ticket_display = "❌ *Chưa thiết lập*"

        embed.add_field(
            name="🎫 Kênh Ticket System",
            value=f"{ticket_display}\n"
                  f"*Kênh để user tạo ticket VND/OwO đổi thưởng*",
            inline=False
        )

        # Hiển thị Leaderboard Channel
        if lb_channel_id:
            lb_channel = self.ctx.guild.get_channel(int(lb_channel_id))
            lb_display = lb_channel.mention if lb_channel else f"~~<#{lb_channel_id}>~~ *(Đã xóa)*"
        else:
            lb_display = "❌ *Chưa thiết lập*"

        embed.add_field(
            name="🏆 Kênh Bảng Xếp Hạng",
            value=f"{lb_display}\n"
                  f"*Bảng xếp hạng tự động cập nhật mỗi 1 giờ*",
            inline=False
        )

        # Hiển thị Event Mưa Bánh Settings
        event_ch_display = "❌ *Chưa thiết lập*"
        event_role_display = "❌ *Chưa thiết lập*"

        if event_channel_id:
            event_channel = self.ctx.guild.get_channel(int(event_channel_id))
            event_ch_display = event_channel.mention if event_channel else f"~~<#{event_channel_id}>~~ *(Đã xóa)*"

        if event_role_id:
            event_role = self.ctx.guild.get_role(int(event_role_id))
            event_role_display = event_role.mention if event_role else f"~~<@&{event_role_id}>~~ *(Đã xóa)*"

        embed.add_field(
            name="🌧️ Sự Kiện Mưa Bánh",
            value=f"**Kênh thông báo:** {event_ch_display}\n"
                  f"**Role ping:** {event_role_display}\n"
                  f"*Event tự động mỗi 12-72h, kéo dài 15-30 phút*",
            inline=False
        )

        # Hiển thị Spawn Channels
        if spawn_channels:
            spawn_display = "\n".join([f"• <#{ch_id}>" for ch_id in spawn_channels[:10]])
            if len(spawn_channels) > 10:
                spawn_display += f"\n*... và {len(spawn_channels) - 10} kênh khác*"
        else:
            spawn_display = "❌ *Chưa thiết lập*"

        embed.add_field(
            name="🎁 Kênh Spawn Vật Phẩm",
            value=f"{spawn_display}\n"
                  f"*Tổng: {len(spawn_channels)} kênh*\n"
                  f"*Bot sẽ tự động rơi nguyên liệu/bánh trong các kênh này*",
            inline=False
        )

        embed.set_footer(
            text=f"Server: {self.ctx.guild.name} | Sử dụng các nút bên dưới để cấu hình",
            icon_url=self.ctx.guild.icon.url if self.ctx.guild.icon else None
        )

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            return embed

    @discord.ui.button(label="📋 Đặt Kênh Log", style=discord.ButtonStyle.primary, emoji="📋")
    async def set_log_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Thiết lập kênh log"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = LogChannelModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="➕ Thêm Kênh Spawn", style=discord.ButtonStyle.green, emoji="🎁")
    async def add_spawn_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Thêm kênh spawn"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = AddSpawnChannelModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="➖ Xóa Kênh Spawn", style=discord.ButtonStyle.red, emoji="🗑️")
    async def remove_spawn_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Xóa kênh spawn"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = RemoveSpawnChannelModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🎫 Setup Ticket", style=discord.ButtonStyle.blurple, emoji="🎫", row=1)
    async def setup_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Setup ticket system"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = TicketChannelModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🏆 Setup Leaderboard", style=discord.ButtonStyle.blurple, emoji="🏆", row=1)
    async def setup_leaderboard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Setup leaderboard"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = LeaderboardChannelModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🌧️ Setup Event", style=discord.ButtonStyle.blurple, emoji="🌧️", row=1)
    async def setup_event_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Setup event Mưa Bánh"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể thay đổi cài đặt!", ephemeral=True)
            return

        modal = EventSettingsModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔄 Làm Mới", style=discord.ButtonStyle.gray, emoji="🔄", row=2)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Làm mới hiển thị"""
        await self.update_embed(interaction)

    @discord.ui.button(label="❌ Đóng", style=discord.ButtonStyle.gray, emoji="❌", row=2)
    async def close_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Đóng menu settings"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Chỉ Admin mới có thể đóng menu!", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="⚙️ Menu Cài Đặt Đã Đóng",
            description="Dùng lệnh `esettings` để mở lại menu cài đặt.",
            color=discord.Color.gray()
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        """Xử lý khi hết timeout"""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                embed = self.message.embeds[0]
                embed.color = discord.Color.gray()
                embed.set_footer(text="⏳ Menu đã hết hạn. Dùng !settings để mở lại.")
                await self.message.edit(embed=embed, view=self)
            except:
                pass

# ============================================
# MODAL DIALOGS
# ============================================

class LogChannelModal(discord.ui.Modal):
    """Modal để nhập channel ID cho log channel"""
    def __init__(self, settings_view):
        super().__init__(title="Đặt Kênh Log Admin")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh hoặc Mention Kênh",
            placeholder="Ví dụ: 1260125199324549220 hoặc #log-admin",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()

        # Parse channel ID từ mention hoặc raw ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        # Kiểm tra channel có tồn tại không
        try:
            channel = interaction.guild.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    f"❌ Không tìm thấy kênh với ID: `{channel_id}`\n"
                    f"*Vui lòng kiểm tra lại ID hoặc quyền của bot.*",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ! Vui lòng nhập đúng định dạng số.",
                ephemeral=True
            )
            return

        # Lưu vào database
        database.set_setting("log_channel_id", channel_id)

        await interaction.response.send_message(
            f"✅ Đã đặt kênh log thành công: {channel.mention}",
            ephemeral=True
        )

        # Cập nhật embed
        await self.settings_view.update_embed()

class AddSpawnChannelModal(discord.ui.Modal):
    """Modal để thêm spawn channel"""
    def __init__(self, settings_view):
        super().__init__(title="Thêm Kênh Spawn Vật Phẩm")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh hoặc Mention Kênh",
            placeholder="Ví dụ: 1234567890 hoặc #chat-chung",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()

        # Parse channel ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        try:
            channel = interaction.guild.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    f"❌ Không tìm thấy kênh với ID: `{channel_id}`",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ!",
                ephemeral=True
            )
            return

        # Thêm vào database
        database.add_spawn_channel(channel_id)

        await interaction.response.send_message(
            f"✅ Đã thêm kênh spawn: {channel.mention}",
            ephemeral=True
        )

        await self.settings_view.update_embed()

class RemoveSpawnChannelModal(discord.ui.Modal):
    """Modal để xóa spawn channel"""
    def __init__(self, settings_view):
        super().__init__(title="Xóa Kênh Spawn Vật Phẩm")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh hoặc Mention Kênh cần xóa",
            placeholder="Ví dụ: 1234567890 hoặc #chat-chung",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()

        # Parse channel ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        try:
            int(channel_id)  # Validate it's a number
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ!",
                ephemeral=True
            )
            return

        # Xóa khỏi database
        database.remove_spawn_channel(channel_id)

        await interaction.response.send_message(
            f"✅ Đã xóa kênh spawn: <#{channel_id}>",
            ephemeral=True
        )

        await self.settings_view.update_embed()

class TicketChannelModal(discord.ui.Modal):
    """Modal để setup ticket system trong một channel"""
    def __init__(self, settings_view):
        super().__init__(title="Setup Ticket System")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh để gửi Ticket Panel",
            placeholder="Ví dụ: 1234567890 hoặc #ticket-panel",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()

        # Parse channel ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        try:
            channel = interaction.guild.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    f"❌ Không tìm thấy kênh với ID: `{channel_id}`",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ!",
                ephemeral=True
            )
            return

        # Gửi ticket panel vào channel đó
        try:
            # Import view từ ticket.py
            from ticket import CreateTicketView

            embed = discord.Embed(
                title="🏆 ĐỔI THƯỞNG EVENT",
                description=(
                    "> Nơi biến những hộp bánh trung thu bạn đã vất vả chế tạo được thành giá trị thực tế!\n\n"
                    "**__Các phần quà đổi thưởng:__**\n"
                    "• 10.000 💵 == 5 🎁 `Hộp bánh`\n"
                    "*số lượng: 20*\n"
                    "• 1m 🎮 OwO == 1 🎁 `Hộp bánh`\n"
                    "*số lượng: 50*\n\n"
                    "Hãy nhấn vào nút **Nhận Thưởng Event** phía dưới để bắt đầu gửi yêu cầu nhận quà.\n\n"
                    "📌 **Lưu ý quan trọng khi mở đơn:**\n"
                    "• Chuẩn bị sẵn hình ảnh/bằng chứng.\n"
                    "• Ghi rõ tên tài khoản game / loại quà bạn muốn đổi."
                ),
                color=discord.Color.from_rgb(255, 127, 80)
            )

            bot = interaction.client
            view = CreateTicketView(bot)
            await channel.send(embed=embed, view=view)

            # Lưu vào database
            database.set_setting("ticket_channel_id", channel_id)

            await interaction.response.send_message(
                f"✅ Đã gửi Ticket Panel vào {channel.mention}!\n"
                f"💡 Nhớ setup thêm:\n"
                f"• `eticket setcategory <ID_Category>` - Category chứa ticket\n"
                f"• `eticket settranscript <#Kênh>` - Kênh lưu log\n"
                f"• `eticket addrole <@Role>` - Role được duyệt thưởng",
                ephemeral=True
            )

            await self.settings_view.update_embed()

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Có lỗi xảy ra: {str(e)}",
                ephemeral=True
            )

class LeaderboardChannelModal(discord.ui.Modal):
    """Modal để setup leaderboard trong một channel"""
    def __init__(self, settings_view):
        super().__init__(title="Setup Leaderboard")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh để gửi Leaderboard",
            placeholder="Ví dụ: 1234567890 hoặc #leaderboard",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()

        # Parse channel ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        try:
            channel = interaction.guild.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    f"❌ Không tìm thấy kênh với ID: `{channel_id}`",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ!",
                ephemeral=True
            )
            return

        # Gửi leaderboard vào channel đó
        try:
            await interaction.response.defer(ephemeral=True)

            # Import leaderboard cog
            from leaderboard import Leaderboard
            from datetime import datetime

            bot = interaction.client
            lb_cog = bot.get_cog("Leaderboard")

            if not lb_cog:
                await interaction.followup.send(
                    "❌ Leaderboard cog chưa được load!",
                    ephemeral=True
                )
                return

            # Tạo nội dung leaderboard
            leaderboard_text = await lb_cog.create_leaderboard_text()

            # Gửi vào channel
            lb_message = await channel.send(content=leaderboard_text)

            # Lưu vào database
            database.set_setting("lb_channel_id", str(channel.id))
            database.set_setting("lb_message_id", str(lb_message.id))

            await interaction.followup.send(
                f"✅ Đã gửi Leaderboard vào {channel.mention}!\n"
                f"🔄 Bảng xếp hạng sẽ tự động cập nhật mỗi 1 giờ.",
                ephemeral=True
            )

            await self.settings_view.update_embed()

        except Exception as e:
            await interaction.followup.send(
                f"❌ Có lỗi xảy ra: {str(e)}",
                ephemeral=True
            )

class EventSettingsModal(discord.ui.Modal):
    """Modal để setup event Mưa Bánh"""
    def __init__(self, settings_view):
        super().__init__(title="Setup Event Mưa Bánh")
        self.settings_view = settings_view

        self.channel_input = discord.ui.TextInput(
            label="ID Kênh thông báo Event",
            placeholder="Ví dụ: 1234567890 hoặc #announcements",
            required=True,
            max_length=50
        )
        self.add_item(self.channel_input)

        self.role_input = discord.ui.TextInput(
            label="ID Role để Ping (tùy chọn)",
            placeholder="Ví dụ: 1234567890 hoặc @Event hoặc để trống",
            required=False,
            max_length=50
        )
        self.add_item(self.role_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()
        role_input = self.role_input.value.strip()

        # Parse channel ID
        channel_id = None
        if channel_input.startswith("<#") and channel_input.endswith(">"):
            channel_id = channel_input[2:-1]
        else:
            channel_id = channel_input.replace("#", "").strip()

        try:
            channel = interaction.guild.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    f"❌ Không tìm thấy kênh với ID: `{channel_id}`",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ ID kênh không hợp lệ!",
                ephemeral=True
            )
            return

        # Parse role ID (tùy chọn)
        role_id = None
        if role_input:
            if role_input.startswith("<@&") and role_input.endswith(">"):
                role_id = role_input[3:-1]
            else:
                role_id = role_input.replace("@", "").strip()

            try:
                role = interaction.guild.get_role(int(role_id))
                if not role:
                    await interaction.response.send_message(
                        f"❌ Không tìm thấy role với ID: `{role_id}`",
                        ephemeral=True
                    )
                    return
            except ValueError:
                await interaction.response.send_message(
                    "❌ ID role không hợp lệ!",
                    ephemeral=True
                )
                return

        # Lưu vào database
        database.set_setting("event_channel_id", channel_id)
        if role_id:
            database.set_setting("event_role_id", role_id)

        role_text = f" và role <@&{role_id}>" if role_id else ""
        await interaction.response.send_message(
            f"✅ Đã setup Event Mưa Bánh!\n"
            f"📢 Kênh thông báo: {channel.mention}{role_text}\n\n"
            f"💡 **Lệnh quản lý event:**\n"
            f"• `emuabanh on` - Bật event ngay\n"
            f"• `emuabanh off` - Tắt event\n"
            f"• `emuabanh status` - Xem trạng thái",
            ephemeral=True
        )

        await self.settings_view.update_embed()

# ============================================
# COMMAND COG
# ============================================

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="⚙️ Mở menu cài đặt bot")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def settings_slash(self, interaction: discord.Interaction):
        """Mở menu cài đặt bot (Admin only) - Slash Command"""
        # Tạo fake ctx object để tương thích với SettingsView
        class FakeContext:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.channel = interaction.channel
                self.author = interaction.user

        fake_ctx = FakeContext(interaction)
        view = SettingsView(fake_ctx)
        embed = await view.update_embed()

        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @commands.command(name="settings", aliases=["caidat", "setup"])
    @commands.has_permissions(administrator=True)
    async def settings_command(self, ctx):
        """Mở menu cài đặt bot (Admin only) - Prefix Command (legacy)"""
        view = SettingsView(ctx)
        embed = await view.update_embed()
        view.message = await ctx.send(embed=embed, view=view)

    @settings_command.error
    async def settings_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn cần quyền **Administrator** để sử dụng lệnh này!")

async def setup(bot):
    await bot.add_cog(Settings(bot))
