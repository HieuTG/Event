import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import database

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX")

# Initialize Rich Console for aesthetic terminal outputs
console = Console()

# Setup bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands
intents.members = True          # Useful for store customer tracking

# Initialize Bot (disable default help command to use our custom one)
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

async def load_extensions():
    """Dynamically loads all .py files from the Commands folder."""
    console.print("\n[bold cyan]🔄 Loading Commands...[/bold cyan]")
    
    table = Table(title="Module Loading Status", show_header=True, header_style="bold magenta")
    table.add_column("Command File", style="dim", width=20)
    table.add_column("Status", justify="right")

    for filename in os.listdir('./Commands'):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = f'Commands.{filename[:-3]}'
            try:
                await bot.load_extension(module_name)
                table.add_row(filename, "[bold green]✔ Loaded[/bold green]")
            except Exception as e:
                table.add_row(filename, f"[bold red]✖ Failed: {e}[/bold red]")
    
    console.print(table)

@bot.event
async def on_ready():
    """Triggers when the bot successfully connects to Discord."""
    # Set a custom store status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over the Server Store 🛒"
        )
    )

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        console.print(f"[bold green]✓ Synced {len(synced)} slash command(s)[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to sync slash commands: {e}[/bold red]")

    # Aesthetic terminal dashboard
    dashboard = Panel.fit(
        f"[bold green]Bot is Online and Ready![/bold green]\n"
        f"[white]Logged in as:[/white] [cyan]{bot.user} (ID: {bot.user.id})[/cyan]\n"
        f"[white]Connected Servers:[/white] [yellow]{len(bot.guilds)}[/yellow]\n"
        f"[white]Command Prefix:[/white] [red]{PREFIX}[/red]",
        title="[bold blue]🚀 System Status[/bold blue]",
        border_style="green"
    )
    console.print(dashboard)

async def main():
    """Main async entry point to start the bot."""
    # Khởi tạo database tại đây để tạo bảng ngay khi bật bot
    database.init_db() 
    
    async with bot:
        await load_extensions()
        if not TOKEN:
            console.print("[bold red]ERROR: DISCORD_TOKEN not found in .env file![/bold red]")
            return
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Bot shut down by user.[/bold red]")