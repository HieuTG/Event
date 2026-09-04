import discord
from discord.ext import commands, tasks
import random
import asyncio
import time
import database

# Danh sách tỷ lệ rớt nguyên liệu
DROP_ITEMS = {
    "manh_vo": ("<:manhvo:1523760564663222382> Mảnh Bánh Vỡ", 30),
    "dau_xanh": ("<:dx_icon:1523756971738529802> Đậu Xanh", 20),
    "thap_cam": ("<:tc_icon:1523756962930757712> Thập Cẩm", 20),
    "me_den": ("<:md_icon:1523756996858351756> Mè Đen", 15),
    "khoai_mon": ("<:km_icon:1523756985047060734> Khoai Môn", 10),
    "hat_sen": ("<:hs_icon:1523756991879839994> Hạt Sen", 4),
    "trung_muoi": ("<:tm_icon:1523756978663325706> Trứng Muối (HIẾM)", 1)
}

# =========================================================================
# 1. GIAO DIỆN NÚT BẤM "NHẶT"
# =========================================================================
class GrabBoxView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300) 
        self.is_grabbed = False
        self.message = None

    @discord.ui.button(label="🧤 NHẶT NGAY!", style=discord.ButtonStyle.success, emoji="🎁")
    async def grab_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_grabbed:
            await interaction.response.send_message("💨 Tiếc quá! Ai đó đã nhanh tay hơn bạn mất rồi!", ephemeral=True)
            return

        self.is_grabbed = True
        self.stop()

        item_keys = list(DROP_ITEMS.keys())
        weights = [info[1] for info in DROP_ITEMS.values()]
        reward_key = random.choices(item_keys, weights=weights, k=1)[0]
        reward_name = DROP_ITEMS[reward_key][0]

        user_id = str(interaction.user.id)
        database.add_item_to_inventory(user_id, reward_key, 1)

        button.disabled = True
        button.label = "ĐÃ ĐƯỢC NHẶT"
        button.style = discord.ButtonStyle.secondary

        embed = discord.Embed(
            title="<a:Checkmark:1524819406385840158> HỘP BÁNH ĐÃ ĐƯỢC NHẶT!",
            description=f"<a:emojigg_1:1524819952089960649> {interaction.user.mention} đã nhanh tay nhặt hộp quà và nhận được **{reward_name}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text="🧹 Tin nhắn này sẽ tự hủy sau 15 giây để dọn rác kênh chat.")
        await interaction.response.edit_message(embed=embed, view=self)

        await asyncio.sleep(15)
        try:
            if self.message:
                await self.message.delete()
        except discord.NotFound:
            pass

    async def on_timeout(self):
        if not self.is_grabbed and self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

# =========================================================================
# 2. COG CHÍNH: SPAWN BÁNH & EVENT MƯA BÁNH
# =========================================================================
class BoxSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Biến trạng thái cho Spawn
        self.time_since_last_spawn = 0
        self.current_target_sleep = random.randint(900, 3600) # Mặc định 15 - 60p

        # Biến trạng thái cho Event Mưa Bánh
        self.is_event_active = False
        self.event_end_time = 0
        # Đặt lịch Event tiếp theo (24h - 72h tính từ lúc bật bot)
        self.next_event_time = time.time() + random.randint(24 * 3600, 3 * 24 * 3600)
        self.event_message_id = None
        self.event_channel_id = None

        # Khởi động các vòng lặp
        self.auto_spawn_loop.start()
        self.event_scheduler_loop.start()

    def cog_unload(self):
        self.auto_spawn_loop.cancel()
        self.event_scheduler_loop.cancel()

    # --- HÀM THẢ BÁNH CHÍNH ---
    async def trigger_box_spawn(self):
        channels = database.get_all_spawn_channels()
        if not channels:
            return

        channel_id = random.choice(channels)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="<:holiday_crate:1523749995059216494> MỘT HỘP QUÀ TRUNG THU BẤT NGỜ XUẤT HIỆN!",
            description="> Hằng Nga vừa đánh rơi một hộp nguyên liệu bí ẩn!\n<a:PinkRightArrowBounce:1524817060608086067>  Nhặt nhanh trước khi người khác cướp mất!",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1260125199324549220/1524816161479459087/ezgif.com-remove-background_1.gif?ex=6a511f36&is=6a4fcdb6&hm=10c3d8a44456269425dbb59c131b7a97fab47335da58b3086858afe04c5bb16f&=&width=800&height=800")
        embed.set_footer(text="Hộp quà sẽ tự biến mất sau 5 phút.")

        view = GrabBoxView()
        try:
            msg = await channel.send(embed=embed, view=view)
            view.message = msg
        except Exception:
            pass

    # =========================================================================
    # VÒNG LẶP ĐẾM NHỊP THẢ BÁNH (CHẠY MỖI 5 GIÂY)
    # =========================================================================
    @tasks.loop(seconds=5)
    async def auto_spawn_loop(self):
        self.time_since_last_spawn += 5

        # Nếu đã đạt đủ thời gian chờ -> Thả bánh
        if self.time_since_last_spawn >= self.current_target_sleep:
            await self.trigger_box_spawn()
            
            # Reset thời gian đếm
            self.time_since_last_spawn = 0
            
            # Bốc thăm thời gian ngủ cho hộp tiếp theo dựa vào trạng thái Event
            if self.is_event_active:
                self.current_target_sleep = random.randint(60, 120) # Event: 1 - 2 phút
            else:
                self.current_target_sleep = random.randint(900, 3600) # Thường: 15 - 60 phút

    @auto_spawn_loop.before_loop
    async def before_auto_spawn(self):
        await self.bot.wait_until_ready()

    # =========================================================================
    # HỆ THỐNG EVENT MƯA BÁNH (KÍCH HOẠT VÀ TẮT)
    # =========================================================================
    async def start_cake_rain(self):
        self.is_event_active = True
        self.time_since_last_spawn = 9999 # Ép thả bánh NGAY LẬP TỨC

        channel_id = database.get_setting("event_channel_id")
        role_id = database.get_setting("event_role_id")

        if channel_id:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                mention_text = f"<@&{role_id}>" if role_id else "@here"
                embed = discord.Embed(
                    title="<a:tada_left:1523846290927124490> SỰ KIỆN MƯA BÁNH TRUNG THU XUẤT HIỆN! <a:tada_right:1523846292105724035>",
                    description=f"> Bầu trời bỗng chuyển màu xám nhạt, gió đêm rằm khẽ lay động cành cây. Mây đen kéo về che kín ánh trăng, và... một cơn mưa lạ sắp đổ xuống.\n⋆｡‧˚ʚ🥮ɞ‧₊˚⋆\n\n*🌧️ Không phải mưa nước*\n*mà là **mưa bánh trung thu!***\n\n**__Hiệu ứng:__**\n⏳ Tốc độ rơi: **1-2 phút/hộp**.\n\nTham gia ngay trước khi sự kiện kết thúc sau 15-30 phút nữa!",
                    color=discord.Color.from_rgb(255, 153, 0)
                )
                embed.set_image(url="https://images-ext-1.discordapp.net/external/ga3r-8sQjWvIrXYEUOsvO6qs9QHc7Nb-kskIKdeZZQw/https/media0.giphy.com/media/v1.Y2lkPTZjMDliOTUyOGl3ZDUwMno1MHAxN2d4Y2dndzI0MGlpNjdoaDV4bGY5aWpvNWt5ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oEdv6UTqzNk9Y5i36/giphy.gif")
                embed.set_footer(text=time.strftime("⏰ Bắt đầu lúc: %H:%M:%S • %d/%m/%Y", time.localtime()))
                try:
                    msg = await channel.send(content=f"<a:exc:1523747494805110814> Thông báo sự kiện: {mention_text}", embed=embed)
                    self.event_message_id = msg.id
                    self.event_channel_id = channel.id
                    print(f"✅ [MƯA BÁNH] Đã gửi thông báo event tới kênh {channel.name} (ID: {channel.id})")
                except Exception as e:
                    print(f"❌ [MƯA BÁNH] Lỗi khi gửi thông báo: {e}")
            else:
                print(f"❌ [MƯA BÁNH] Không tìm thấy kênh với ID: {channel_id}")
        else:
            print(f"⚠️ [MƯA BÁNH] Chưa set kênh thông báo event! Dùng: emuabanh setchannel #kênh")

    async def stop_cake_rain(self):
        self.is_event_active = False
        self.current_target_sleep = random.randint(900, 3600) # Đưa về tốc độ cũ
        
        # Xóa tin nhắn thông báo sự kiện cũ
        if self.event_message_id and self.event_channel_id:
            try:
                channel = self.bot.get_channel(self.event_channel_id)
                msg = await channel.fetch_message(self.event_message_id)
                await msg.delete()
            except Exception:
                pass
            self.event_message_id = None

    @tasks.loop(seconds=10)
    async def event_scheduler_loop(self):
        now = time.time()
        
        # Đã đến giờ kích hoạt event chưa?
        if not self.is_event_active and now >= self.next_event_time:
            await self.start_cake_rain()
            self.event_end_time = now + random.randint(15 * 60, 30 * 60) # Kéo dài 15-30p

        # Đã hết giờ event chưa?
        elif self.is_event_active and now >= self.event_end_time:
            await self.stop_cake_rain()
            self.next_event_time = now + random.randint(12 * 3600, 3 * 24 * 3600) # Đặt lịch tiếp

    @event_scheduler_loop.before_loop
    async def before_event_scheduler(self):
        await self.bot.wait_until_ready()

    # =========================================================================
    # LỆNH ADMIN QUẢN LÝ EVENT (!muabanh)
    # =========================================================================
    @commands.group(name="muabanh", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def muabanh_cmd(self, ctx):
        await ctx.send("👉 Dùng: `emuabanh on/off/status` hoặc `emuabanh setchannel <#kênh>` / `emuabanh setrole <@role>`")

    @muabanh_cmd.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def muabanh_setchannel(self, ctx, channel: discord.TextChannel):
        database.set_setting("event_channel_id", str(channel.id))
        await ctx.send(f"✅ Đã chọn kênh {channel.mention} làm nơi thông báo Sự Kiện Mưa Bánh!")

    @muabanh_cmd.command(name="setrole")
    @commands.has_permissions(administrator=True)
    async def muabanh_setrole(self, ctx, role: discord.Role):
        database.set_setting("event_role_id", str(role.id))
        await ctx.send(f"✅ Đã chọn role {role.mention} để Ping khi Mưa Bánh bắt đầu!")

    @muabanh_cmd.command(name="on")
    @commands.has_permissions(administrator=True)
    async def muabanh_on(self, ctx):
        if self.is_event_active:
            await ctx.send("❌ Sự kiện Mưa Bánh ĐANG diễn ra rồi!")
            return
        await ctx.send("🌩️ **Admin đã cưỡng chế kích hoạt Mưa Bánh ngay lập tức!**")
        self.event_end_time = time.time() + random.randint(15 * 60, 30 * 60)
        await self.start_cake_rain()

    @muabanh_cmd.command(name="off")
    @commands.has_permissions(administrator=True)
    async def muabanh_off(self, ctx):
        if not self.is_event_active:
            await ctx.send("❌ Đang không có sự kiện nào diễn ra.")
            return
        await self.stop_cake_rain()
        # Đặt lại lịch cho event tiếp theo
        self.next_event_time = time.time() + random.randint(12 * 3600, 3 * 24 * 3600)
        await ctx.send("🛑 **Đã kết thúc Sự Kiện Mưa Bánh! Tốc độ rơi đã trở về bình thường.**")

    @muabanh_cmd.command(name="status", aliases=["check"])
    @commands.has_permissions(administrator=True)
    async def muabanh_status(self, ctx):
        now = time.time()
        if self.is_event_active:
            time_left = int(self.event_end_time - now)
            mins, secs = divmod(time_left, 60)
            await ctx.send(f"🌩️ **SỰ KIỆN ĐANG DIỄN RA!**\n⏳ Còn lại: `{mins} phút {secs} giây`.\n🚀 Tốc độ thả hiện tại: `1-2 phút/hộp` (Sẽ thả hộp tiếp theo trong `< {self.current_target_sleep - self.time_since_last_spawn} giây` nữa)")
        else:
            time_wait = int(self.next_event_time - now)
            hours, remainder = divmod(time_wait, 3600)
            mins, _ = divmod(remainder, 60)
            await ctx.send(f"😴 Đang ở chế độ rớt thường.\n⏰ Sự kiện Mưa Bánh tự động tiếp theo sẽ bắt đầu sau khoảng: `{hours} giờ {mins} phút`.")

    # [GIỮ NGUYÊN CÁC LỆNH !spawn CŨ]
    @commands.group(name="spawn", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def spawn_cmd(self, ctx):
        channels = database.get_all_spawn_channels()
        if not channels:
            await ctx.send("📭 **Hiện chưa có kênh thả bánh!** Dùng: `espawn add <#kênh>`")
            return
        mentions = [f"<#{cid}>" for cid in channels]
        await ctx.send(f"📋 **Kênh thả bánh ({len(channels)}):** " + ", ".join(mentions))

    @spawn_cmd.command(name="add")
    @commands.has_permissions(administrator=True)
    async def spawn_add(self, ctx, channel: discord.TextChannel):
        database.add_spawn_channel(str(channel.id))
        await ctx.send(f"✅ Đã thêm kênh {channel.mention} vào danh sách thả bánh!")

    @spawn_cmd.command(name="remove", aliases=["del", "rm"])
    @commands.has_permissions(administrator=True)
    async def spawn_remove(self, ctx, channel: discord.TextChannel):
        database.remove_spawn_channel(str(channel.id))
        await ctx.send(f"❌ Đã xóa kênh {channel.mention} khỏi danh sách thả bánh.")

    @spawn_cmd.command(name="test")
    @commands.has_permissions(administrator=True)
    async def spawn_test(self, ctx):
        await ctx.send("🚀 **Test thả bánh...**", delete_after=3)
        await self.trigger_box_spawn()

async def setup(bot):
    await bot.add_cog(BoxSpawnCog(bot))