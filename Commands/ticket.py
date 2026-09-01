import discord
from discord.ext import commands
import database
import time
import asyncio
import io # Thêm thư viện io để tạo file txt trực tiếp trên RAM

# =========================================================================
# HÀM TRỢ GIÚP XỬ LÝ DATABASE
# =========================================================================
def get_support_roles():
    raw = database.get_setting("ticket_support_roles")
    if not raw:
        return []
    return [int(rid.strip()) for rid in raw.split(",") if rid.strip().isdigit()]

def save_support_roles(role_ids: list):
    raw_str = ",".join(str(rid) for rid in role_ids)
    database.set_setting("ticket_support_roles", raw_str)


# =========================================================================
# 1. VIEW ĐỂ TẠO TICKET
# =========================================================================
class CreateTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Nhận Thưởng Event", 
        style=discord.ButtonStyle.success, 
        emoji="🎁", 
        custom_id="btn_create_event_ticket"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        category_id = database.get_setting("ticket_category_id")
        role_ids = get_support_roles()

        if not category_id or not role_ids:
            await interaction.followup.send("❌ Hệ thống chưa được thiết lập hoàn tất! (Chưa cài Category hoặc chưa thêm Role hỗ trợ nào)", ephemeral=True)
            return

        category = guild.get_channel(int(category_id))
        if not category:
            await interaction.followup.send("❌ Không tìm thấy danh mục chứa Ticket, vui lòng báo Admin.", ephemeral=True)
            return

        current_counter = database.get_setting("ticket_counter")
        next_val = int(current_counter) + 1 if current_counter else 1
        database.set_setting("ticket_counter", str(next_val))

        channel_name = f"đổi-thưởng-{next_val:04d}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        activated_roles = []
        for r_id in role_ids:
            role = guild.get_role(r_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
                activated_roles.append(role)

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket đổi thưởng của {user.name} | Số: #{next_val:04d}"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Có lỗi xảy ra khi tạo kênh: {e}", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Đã tạo ticket thành công tại {ticket_channel.mention}!", ephemeral=True)

        ping_roles_str = " ".join(role.mention for role in activated_roles)
        ping_content = f"{ping_roles_str} {user.mention}"
        
        embed = discord.Embed(
            title=f"🎁 TICKET ĐỔI THƯỞNG EVENT - #{next_val:04d}",
            description=(
                f"Chào mừng {user.mention} đến với kênh tiếp nhận đổi thưởng!\n\n"
                "**Bạn muốn đổi gì thì nói luôn nè!!**"
            ),
            color=discord.Color.from_rgb(255, 127, 80)
        )
        embed.add_field(name="👤 Người yêu cầu", value=user.mention, inline=True)
        embed.add_field(name="⏰ Thời gian mở", value=f"<t:{int(time.time())}:F>", inline=True)
        embed.add_field(name="📌 Trạng thái", value="🟢 Đang chờ duyệt...", inline=True)
        embed.set_footer(text="Hệ thống tự động • Vui lòng chuẩn bị sẵn bằng chứng")

        control_view = TicketControlView(self.bot)
        await ticket_channel.send(content=ping_content, embed=embed, view=control_view)


# =========================================================================
# 2. FORM ĐIỀN THÔNG TIN KHI ĐÓNG TICKET (MODAL) VÀ TẠO TRANSCRIPT
# =========================================================================
class CloseTicketModal(discord.ui.Modal, title="Xác Nhận Đóng & Trao Thưởng"):
    reward_info = discord.ui.TextInput(
        label="Đã đổi thưởng gì?",
        style=discord.TextStyle.paragraph,
        placeholder="VD: 10k hoặc 1m owo",
        required=True,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # Thông báo chờ (Defer) vì quá trình trích xuất transcript có thể tốn vài giây
        await interaction.response.defer()

        channel = interaction.channel
        closer = interaction.user
        
        # --- BƯỚC 1: Lấy toàn bộ lịch sử tin nhắn trong kênh ---
        messages = [msg async for msg in channel.history(limit=None, oldest_first=True)]
        
        # Trích xuất người yêu cầu từ Embed đầu tiên của bot
        creator_mention = "Không xác định"
        for msg in messages:
            if msg.author == self.bot.user and msg.embeds:
                for field in msg.embeds[0].fields:
                    if "Người yêu cầu" in field.name:
                        creator_mention = field.value
                        break
                if creator_mention != "Không xác định":
                    break

        # --- BƯỚC 2: Định dạng nội dung file Transcript ---
        transcript_text = f"=== TICKET TRANSCRIPT: {channel.name.upper()} ===\n"
        transcript_text += f"Ngày đóng: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n"
        transcript_text += f"Người đóng: {closer.name} ({closer.id})\n"
        transcript_text += f"Phần thưởng đã duyệt: {self.reward_info.value}\n"
        transcript_text += "="*50 + "\n\n"

        for msg in messages:
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M")
            content = msg.clean_content
            # Kèm link ảnh nếu có
            if msg.attachments:
                content += f" [Đính kèm: {', '.join(a.url for a in msg.attachments)}]"
            transcript_text += f"[{time_str}] {msg.author.name}: {content}\n"

        # Đóng gói chuỗi text thành một file có thể gửi đi
        file_bytes = io.BytesIO(transcript_text.encode('utf-8'))
        discord_file = discord.File(file_bytes, filename=f"transcript-{channel.name}.txt")

        # --- BƯỚC 3: Gửi Transcript về kênh lưu trữ ---
        transcript_ch_id = database.get_setting("ticket_transcript_channel_id")
        if transcript_ch_id:
            transcript_ch = interaction.guild.get_channel(int(transcript_ch_id))
            if transcript_ch:
                embed = discord.Embed(
                    title="📜 LƯU TRỮ TICKET ĐỔI THƯỞNG",
                    color=discord.Color.red()
                )
                embed.add_field(name="🆔 Kênh Ticket", value=f"`{channel.name}`", inline=True)
                embed.add_field(name="👤 Người mở", value=creator_mention, inline=True)
                embed.add_field(name="🔒 Người đóng", value=closer.mention, inline=True)
                embed.add_field(name="🎁 Chi tiết phần thưởng", value=f"```\n{self.reward_info.value}\n```", inline=False)
                
                await transcript_ch.send(embed=embed, file=discord_file)

        # --- BƯỚC 4: Xóa kênh Ticket ---
        await interaction.followup.send("🔒 **Đã lưu Transcript. Kênh sẽ tự động xóa sau 5 giây...**")
        await asyncio.sleep(5)
        try:
            await channel.delete()
        except Exception:
            pass


# =========================================================================
# 3. VIEW ĐIỀU KHIỂN TICKET (Trong kênh đổi thưởng)
# =========================================================================
class TicketControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Đổi thưởng", 
        style=discord.ButtonStyle.success, 
        emoji="<:holiday_crate:1523749995059216494>", 
        custom_id="btn_claim_ticket"
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_ids = get_support_roles()
        user_role_ids = [r.id for r in interaction.user.roles]
        is_staff = any(r_id in user_role_ids for r_id in role_ids) or interaction.user.guild_permissions.administrator

        if not is_staff:
            await interaction.response.send_message("❌ Bạn không có quyền hạn duyệt đơn đổi thưởng này!", ephemeral=True)
            return

        message = interaction.message
        embed = message.embeds[0]
        for field in embed.fields:
            if field.name == "📌 Trạng thái" and "Đang duyệt bởi" in field.value:
                await interaction.response.send_message("❌ Đơn này đã được một Staff khác nhận xử lý từ trước!", ephemeral=True)
                return

        embed.set_field_at(2, name="📌 Trạng thái", value=f"🟡 Đang duyệt bởi {interaction.user.mention}", inline=True)
        button.disabled = True
        button.label = "Đang xử lý..."
        button.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.channel.send(f"🤝 **{interaction.user.mention}** đã tiếp nhận và đang tiến hành kiểm tra phần thưởng!")

    @discord.ui.button(
        label="Đóng Ticket", 
        style=discord.ButtonStyle.danger, 
        emoji="🔒", 
        custom_id="btn_close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vô hiệu hóa nút đóng tạm thời để tránh ấn đúp
        button.disabled = True
        await interaction.message.edit(view=self)
        
        # Bật lên một Form điền thông tin thay vì xóa kênh ngay
        modal = CloseTicketModal(self.bot)
        await interaction.response.send_modal(modal)


# =========================================================================
# 4. COG CHÍNH - QUẢN LÝ THIẾT LẬP
# =========================================================================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(CreateTicketView(self.bot))
        self.bot.add_view(TicketControlView(self.bot))

    @commands.group(name="ticket", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ticket_group(self, ctx):
        await ctx.send(
            "🏆 **HƯỚNG DẪN SETUP TICKET ĐỔI THƯỞNG:**\n"
            "• `eticket setcategory <ID_Category>` : Chọn danh mục lưu các ticket.\n"
            "• `eticket settranscript <#Kênh>` : Kênh lưu trữ file log khi đóng ticket.\n"
            "• `eticket addrole <@Role>` / `eticket removerole <@Role>` : Quản lý Role duyệt.\n"
            "• `eticket info` : Xem danh sách các thiết lập hiện tại.\n"
            "• `eticket setup` : Gửi bảng Tạo Đơn Đổi Thưởng ra kênh hiện tại."
        )

    @ticket_group.command(name="settranscript")
    @commands.has_permissions(administrator=True)
    async def ticket_settranscript(self, ctx, channel: discord.TextChannel):
        database.set_setting("ticket_transcript_channel_id", str(channel.id))
        await ctx.send(f"✅ Đã thiết lập kênh lưu trữ Transcript: {channel.mention}")

    @ticket_group.command(name="setcategory")
    @commands.has_permissions(administrator=True)
    async def ticket_setcategory(self, ctx, category: discord.CategoryChannel):
        database.set_setting("ticket_category_id", str(category.id))
        await ctx.send(f"✅ Đã thiết lập danh mục chứa ticket: **{category.name}**")

    @ticket_group.command(name="addrole")
    @commands.has_permissions(administrator=True)
    async def ticket_addrole(self, ctx, role: discord.Role):
        role_ids = get_support_roles()
        if role.id in role_ids:
            return await ctx.send("❌ Role đã có sẵn!")
        role_ids.append(role.id)
        save_support_roles(role_ids)
        await ctx.send(f"✅ Đã thêm Role duyệt thưởng: {role.mention}")

    @ticket_group.command(name="removerole")
    @commands.has_permissions(administrator=True)
    async def ticket_removerole(self, ctx, role: discord.Role):
        role_ids = get_support_roles()
        if role.id not in role_ids:
            return await ctx.send("❌ Role không tồn tại trong danh sách.")
        role_ids.remove(role.id)
        save_support_roles(role_ids)
        await ctx.send(f"✅ Đã xóa Role khỏi danh sách hỗ trợ.")

    @ticket_group.command(name="info")
    @commands.has_permissions(administrator=True)
    async def ticket_info(self, ctx):
        category_id = database.get_setting("ticket_category_id")
        transcript_id = database.get_setting("ticket_transcript_channel_id")
        role_ids = get_support_roles()

        category_str = f"<#{category_id}>" if category_id else "❌ Chưa thiết lập"
        transcript_str = f"<#{transcript_id}>" if transcript_id else "❌ Chưa thiết lập"
        roles_str = ", ".join(f"<@&{rid}>" for rid in role_ids) if role_ids else "❌ Chưa có"

        embed = discord.Embed(title="⚙️ CẤU HÌNH TICKET ĐỔI THƯỞNG", color=discord.Color.blue())
        embed.add_field(name="📂 Danh mục tạo Ticket", value=category_str, inline=False)
        embed.add_field(name="📜 Kênh lưu Transcript", value=transcript_str, inline=False)
        embed.add_field(name="👥 Các Role được duyệt", value=roles_str, inline=False)
        await ctx.send(embed=embed)

    @ticket_group.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        embed = discord.Embed(
            title="🏆 ĐỔI THƯỞNG EVENT",
            description=(
                "> Nơi biến những hộp bánh trung thu bạn đã vất vả chết tạo được thành giá trị thực tế!\n\n"
                "Hãy nhấn vào nút **Nhận Thưởng Event** phía dưới để bắt đầu gửi yêu cầu nhận quà.\n\n"
                "📌 **Lưu ý quan trọng khi mở đơn:**\n"
                "• Đảm bảo bạn phải đủ điều kiện đổi thưởng.\n"
                "• Ghi rõ loại quà bạn muốn đổi."
            ),
            color=discord.Color.from_rgb(255, 127, 80)
        )
        await ctx.send(embed=embed, view=CreateTicketView(self.bot))
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(TicketCog(bot))