import discord
from discord.ext import commands
import database

class Craft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ghep", aliases=["ghepbanh", "craft"])
    async def craft_command(self, ctx):
        """Ghép bộ 6 nguyên liệu thành 1 Hộp Bánh Trung Thu"""
        user_id = str(ctx.author.id)

        # Gọi hàm xử lý từ database
        success = database.craft_mooncakes(user_id)

        if success:
            embed = discord.Embed(
                title="🥮 CHẾ TẠO THÀNH CÔNG!",
                description=f"Chúc mừng {ctx.author.mention}! Bạn đã tiêu hao một bộ 6 nguyên liệu và gói thành công **🎁 1 Hộp Bánh Trung Thu Thượng Hạng**!",
                color=discord.Color.green()
            )
            embed.set_image(url="https://i.pinimg.com/736x/3f/aa/09/3faa09c797d6e37c641be9680692be03.jpg")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ CHẾ TẠO THẤT BẠI",
                description=f"{ctx.author.mention}, bạn chưa tích lũy đủ bộ **6 vị nguyên liệu khác nhau**. Hãy kiểm tra lại bằng lệnh `eruong` nhé!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Craft(bot))