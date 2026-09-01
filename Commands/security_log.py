import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
import os

DB_NAME = "mid_autumn_event.db"

def init_security_tables():
    """Khởi tạo bảng logging và security"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Bảng log các giao dịch trade
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_a_id TEXT NOT NULL,
            user_a_name TEXT,
            item_a TEXT NOT NULL,
            amount_a INTEGER NOT NULL,
            user_b_id TEXT NOT NULL,
            user_b_name TEXT,
            item_b TEXT NOT NULL,
            amount_b INTEGER NOT NULL,
            success INTEGER DEFAULT 1
        )
    """)

    # Bảng log các hành động admin modify
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            admin_id TEXT NOT NULL,
            admin_name TEXT,
            action TEXT NOT NULL,
            target_user_id TEXT NOT NULL,
            target_user_name TEXT,
            item_name TEXT,
            amount INTEGER,
            details TEXT
        )
    """)

    # Bảng theo dõi hành vi đáng ngờ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suspicious_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT,
            activity_type TEXT NOT NULL,
            details TEXT,
            severity TEXT DEFAULT 'LOW'
        )
    """)

    # Bảng rate limiting
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id TEXT NOT NULL,
            command TEXT NOT NULL,
            last_used TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, command)
        )
    """)

    conn.commit()
    conn.close()

def log_trade(user_a_id, user_a_name, item_a, amount_a, user_b_id, user_b_name, item_b, amount_b, success=True):
    """Ghi log giao dịch trade"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO trade_logs
        (timestamp, user_a_id, user_a_name, item_a, amount_a, user_b_id, user_b_name, item_b, amount_b, success)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, user_a_id, user_a_name, item_a, amount_a, user_b_id, user_b_name, item_b, amount_b, int(success)))

    conn.commit()
    conn.close()

def log_admin_action(admin_id, admin_name, action, target_user_id, target_user_name, item_name=None, amount=None, details=None):
    """Ghi log hành động admin"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO admin_logs
        (timestamp, admin_id, admin_name, action, target_user_id, target_user_name, item_name, amount, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, admin_id, admin_name, action, target_user_id, target_user_name, item_name, amount, details))

    conn.commit()
    conn.close()

def log_suspicious_activity(user_id, user_name, activity_type, details, severity="LOW"):
    """Ghi log hành vi đáng ngờ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO suspicious_activity
        (timestamp, user_id, user_name, activity_type, details, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, user_id, user_name, activity_type, details, severity))

    conn.commit()
    conn.close()

def check_rate_limit(user_id, command, max_uses=5, window_minutes=1):
    """
    Kiểm tra rate limit cho một lệnh
    Returns: (allowed: bool, remaining: int, reset_time: str)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now()

    cursor.execute("SELECT last_used, count FROM rate_limits WHERE user_id = ? AND command = ?", (user_id, command))
    row = cursor.fetchone()

    if row is None:
        # Lần đầu dùng lệnh
        cursor.execute("""
            INSERT INTO rate_limits (user_id, command, last_used, count)
            VALUES (?, ?, ?, 1)
        """, (user_id, command, now.isoformat()))
        conn.commit()
        conn.close()
        return True, max_uses - 1, None

    last_used = datetime.fromisoformat(row[0])
    count = row[1]
    time_diff = (now - last_used).total_seconds() / 60  # Phút

    if time_diff >= window_minutes:
        # Reset counter
        cursor.execute("""
            UPDATE rate_limits SET last_used = ?, count = 1
            WHERE user_id = ? AND command = ?
        """, (now.isoformat(), user_id, command))
        conn.commit()
        conn.close()
        return True, max_uses - 1, None

    if count >= max_uses:
        # Vượt quá giới hạn
        reset_time = last_used.timestamp() + (window_minutes * 60)
        conn.close()
        return False, 0, int(reset_time)

    # Tăng counter
    cursor.execute("""
        UPDATE rate_limits SET count = count + 1
        WHERE user_id = ? AND command = ?
    """, (user_id, command))
    conn.commit()
    conn.close()
    return True, max_uses - count - 1, None

def get_user_trade_history(user_id, limit=10):
    """Lấy lịch sử trade của user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, user_a_name, item_a, amount_a, user_b_name, item_b, amount_b, success
        FROM trade_logs
        WHERE user_a_id = ? OR user_b_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows

def detect_suspicious_patterns(user_id):
    """
    Phát hiện các pattern đáng ngờ:
    - Trade quá nhiều trong thời gian ngắn
    - Nhận quá nhiều vật phẩm hiếm từ trade
    - Tăng inventory bất thường
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Kiểm tra số lượng trade trong 1 giờ qua
    one_hour_ago = datetime.now().timestamp() - 3600
    cursor.execute("""
        SELECT COUNT(*) FROM trade_logs
        WHERE (user_a_id = ? OR user_b_id = ?)
        AND datetime(timestamp) >= datetime(?, 'unixepoch')
    """, (user_id, user_id, one_hour_ago))

    trade_count = cursor.fetchone()[0]

    conn.close()

    flags = []
    if trade_count >= 10:
        flags.append(("HIGH_TRADE_FREQUENCY", f"Trade {trade_count} lần trong 1 giờ", "MEDIUM"))

    return flags

class SecurityLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_security_tables()

    @commands.command(name="tradelogs", aliases=["lsutrade"])
    @commands.has_permissions(administrator=True)
    async def view_trade_logs(self, ctx, user: discord.Member = None, limit: int = 10):
        """Xem lịch sử trade của một user (Admin only)"""
        if user is None:
            await ctx.send("❌ Vui lòng mention user cần kiểm tra: `ettradelogs @user`")
            return

        trades = get_user_trade_history(str(user.id), limit)

        if not trades:
            await ctx.send(f"📋 {user.mention} chưa có giao dịch trade nào.")
            return

        embed = discord.Embed(
            title=f"📜 Lịch Sử Trade - {user.name}",
            description=f"Hiển thị {min(len(trades), limit)} giao dịch gần nhất",
            color=discord.Color.blue()
        )

        for i, trade in enumerate(trades[:5], 1):  # Chỉ show 5 trade đầu
            timestamp, user_a, item_a, amt_a, user_b, item_b, amt_b, success = trade
            status = "✅" if success else "❌"

            embed.add_field(
                name=f"{i}. {status} <t:{int(datetime.fromisoformat(timestamp).timestamp())}:R>",
                value=f"`{user_a}` gửi `{amt_a}x {item_a}`\n`{user_b}` gửi `{amt_b}x {item_b}`",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="checkuser", aliases=["kiemtra"])
    @commands.has_permissions(administrator=True)
    async def check_user_security(self, ctx, user: discord.Member):
        """Kiểm tra hành vi đáng ngờ của user (Admin only)"""
        flags = detect_suspicious_patterns(str(user.id))

        embed = discord.Embed(
            title=f"🔍 Kiểm Tra Bảo Mật - {user.name}",
            color=discord.Color.orange() if flags else discord.Color.green()
        )

        if not flags:
            embed.description = "✅ Không phát hiện hành vi đáng ngờ"
        else:
            embed.description = f"⚠️ Phát hiện {len(flags)} cảnh báo:"
            for flag_type, details, severity in flags:
                embed.add_field(
                    name=f"🚨 {severity}: {flag_type}",
                    value=details,
                    inline=False
                )

        await ctx.send(embed=embed)

    @view_trade_logs.error
    @check_user_security.error
    async def security_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn không có quyền Admin để sử dụng lệnh này!")

async def setup(bot):
    await bot.add_cog(SecurityLog(bot))
