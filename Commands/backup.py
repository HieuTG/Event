import discord
from discord.ext import commands, tasks
import shutil
import os
from datetime import datetime
import database

class BackupSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_folder = "./backups"
        self.db_name = "mid_autumn_event.db"

        # Tạo thư mục backups nếu chưa tồn tại
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)

        # Bắt đầu task backup tự động
        self.auto_backup.start()

    def cog_unload(self):
        """Dừng task khi cog bị unload"""
        self.auto_backup.cancel()

    @tasks.loop(hours=24)  # Backup mỗi 24 giờ
    async def auto_backup(self):
        """Task tự động backup database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_folder, backup_filename)

            # Copy database
            shutil.copy2(self.db_name, backup_path)

            # Xóa các backup cũ hơn 7 ngày để tiết kiệm dung lượng
            self.clean_old_backups(days=7)

            print(f"✅ [BACKUP] Database đã được backup thành công: {backup_filename}")

            # Gửi thông báo vào log channel (tùy chọn)
            log_channel_id = database.get_setting("log_channel_id")
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    embed = discord.Embed(
                        title="💾 Backup Database Thành Công",
                        description=f"Database đã được sao lưu tự động.\n\n**File:** `{backup_filename}`\n**Thời gian:** <t:{int(datetime.now().timestamp())}:F>",
                        color=discord.Color.green()
                    )
                    await log_channel.send(embed=embed)

        except Exception as e:
            print(f"❌ [BACKUP ERROR] Lỗi khi backup database: {e}")

    @auto_backup.before_loop
    async def before_auto_backup(self):
        """Đợi bot sẵn sàng trước khi chạy task"""
        await self.bot.wait_until_ready()

    def clean_old_backups(self, days=7):
        """Xóa các file backup cũ hơn số ngày chỉ định"""
        try:
            current_time = datetime.now().timestamp()
            max_age = days * 24 * 60 * 60  # Chuyển đổi ngày sang giây

            for filename in os.listdir(self.backup_folder):
                if filename.startswith("backup_") and filename.endswith(".db"):
                    filepath = os.path.join(self.backup_folder, filename)
                    file_age = current_time - os.path.getmtime(filepath)

                    if file_age > max_age:
                        os.remove(filepath)
                        print(f"🗑️ [BACKUP] Đã xóa backup cũ: {filename}")
        except Exception as e:
            print(f"⚠️ [BACKUP] Lỗi khi dọn dẹp backup cũ: {e}")

    @commands.command(name="backup", aliases=["saoLuu"])
    @commands.has_permissions(administrator=True)
    async def manual_backup(self, ctx):
        """Lệnh backup thủ công cho Admin"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"manual_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_folder, backup_filename)

            shutil.copy2(self.db_name, backup_path)

            embed = discord.Embed(
                title="✅ Backup Thành Công",
                description=f"Database đã được sao lưu thủ công.\n\n**File:** `{backup_filename}`\n**Kích thước:** `{os.path.getsize(backup_path) / 1024:.2f} KB`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Backup Thất Bại",
                description=f"Có lỗi xảy ra khi sao lưu database:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="listbackups", aliases=["dsbackup"])
    @commands.has_permissions(administrator=True)
    async def list_backups(self, ctx):
        """Xem danh sách các file backup"""
        try:
            backups = [f for f in os.listdir(self.backup_folder) if f.endswith(".db")]

            if not backups:
                await ctx.send("📂 Chưa có file backup nào.")
                return

            # Sắp xếp theo thời gian (mới nhất trước)
            backups.sort(reverse=True)

            embed = discord.Embed(
                title="💾 Danh Sách Backup Database",
                description=f"Tổng số backup: **{len(backups)}** file",
                color=discord.Color.blue()
            )

            for i, backup in enumerate(backups[:10], 1):  # Chỉ hiển thị 10 file gần nhất
                filepath = os.path.join(self.backup_folder, backup)
                size = os.path.getsize(filepath) / 1024  # KB
                modified_time = int(os.path.getmtime(filepath))

                embed.add_field(
                    name=f"{i}. {backup}",
                    value=f"📊 Kích thước: `{size:.2f} KB`\n🕒 Thời gian: <t:{modified_time}:R>",
                    inline=False
                )

            if len(backups) > 10:
                embed.set_footer(text=f"... và {len(backups) - 10} file khác")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Lỗi khi lấy danh sách backup: {str(e)}")

    @manual_backup.error
    @list_backups.error
    async def backup_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn không có quyền Admin để sử dụng lệnh này!")

async def setup(bot):
    await bot.add_cog(BackupSystem(bot))
