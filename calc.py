### main.py
import os
from discord.ext import commands
import discord
from dotenv import load_dotenv

# Load .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# Load command cogs
async def load_cogs():
    from commands import furnace, camp, upgrade, misc
    await bot.add_cog(furnace.Furnace(bot))
    await bot.add_cog(camp.Camp(bot))
    await bot.add_cog(upgrade.Upgrade(bot))
    await bot.add_cog(misc.Misc(bot))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")

bot.loop.create_task(load_cogs())
bot.run(TOKEN)


### commands/furnace.py
from discord.ext import commands
from utils.calculator import sum_furnace_rss
from utils.embed import embed_msg

class Furnace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def furnace(self, ctx, start: str, stop: str):
        total, error = sum_furnace_rss(start, stop)
        if error:
            await ctx.send(error)
            return
        user = ctx.author.display_name
        output = embed_msg(start, stop, total, user)
        await ctx.send(embed=output)


### commands/camp.py
from discord.ext import commands
from utils.calculator import sum_camp_rss
from utils.embed import embed_msg

class Camp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def camp(self, ctx, start: str, stop: str):
        total, error = sum_camp_rss(start, stop)
        if error:
            await ctx.send(error)
            return
        user = ctx.author.display_name
        output = embed_msg(start, stop, total, user)
        await ctx.send(embed=output)


### commands/upgrade.py
from discord.ext import commands
from utils.calculator import sum_furnace_rss, sum_camp_rss
from utils.embed import embed_msg_upgrade

class Upgrade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def upgrade(self, ctx, range_str: str, percent: str = "0"):
        try:
            start_str, stop_str = range_str.split("-")
            reduction = int(percent)
            if not 0 <= reduction <= 15:
                await ctx.send("Reduction must be between 0 and 15%.")
                return

            f_total, f_err = sum_furnace_rss(start_str, stop_str)
            c_total, c_err = sum_camp_rss(start_str, stop_str)

            if f_err or c_err:
                await ctx.send(f"Error: {f_err or c_err}")
                return

            def apply_discount(data):
                discounted = {}
                for res, val in data.items():
                    if res in ["Meat", "Coal", "Iron"]:
                        val *= (1 - reduction / 100)
                    discounted[res] = round(val)
                return discounted

            f_discounted = apply_discount(f_total)
            c_discounted = apply_discount({k: v * 3 for k, v in c_total.items()})

            combined = {k: f_discounted.get(k, 0) + c_discounted.get(k, 0) for k in f_discounted}

            embed = embed_msg_upgrade(start_str, stop_str, f_discounted, c_discounted, combined, reduction)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Invalid input or error occurred: {e}")


### utils/calculator.py
from data.charts import charts, training_camp_chart
from utils.parser import normalize_level, custom_level_key

def sum_furnace_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)
    sorted_keys = sorted(charts.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Start level must come before stop level."

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index:stop_index + 1]:
        for resource, value in charts[key].items():
            total[resource] += value

    return total, None

def sum_camp_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)
    sorted_keys = sorted(training_camp_chart.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Start level must come before stop level."

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index:stop_index + 1]:
        for resource, value in training_camp_chart[key].items():
            total[resource] += value

    return total, None


### utils/embed.py
import discord
from data.charts import resource_icons

def embed_msg(start: str, stop: str, total: dict, user = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"`{user}'s` Resource Summary",
        description=f"**From `{start}` to `{stop}`**",
        color=discord.Color.orange()
    )
    for resource in ["Meat", "Coal", "Iron", "Fire Crystal", "Refined Crystal"]:
        amount = total.get(resource, 0)
        if resource == "Refined Crystal" and amount == 0:
            continue
        if amount > 0:
            amount = round(amount, 1)
        emoji = resource_icons.get(resource, "")
        suffix = "M" if resource in ["Meat", "Coal", "Iron"] else ""
        embed.add_field(name=resource, value=f"{emoji} {amount}{suffix}", inline=False)

    if user:
        embed.set_footer(text="Happy hoarding~")
    return embed

def embed_msg_upgrade(start, stop, furnace, camp, total, percent):
    embed = discord.Embed(
        title="Total Upgrade Cost",
        description=f"From `{start}` to `{stop}` with `{percent}%` discount",
        color=discord.Color.red()
    )
    for title, section in zip(["Furnace", "Training Camps", "Total"], [furnace, camp, total]):
        text = "\n".join(
            f"{resource_icons.get(res, '')} **{res}**: {val}{'M' if res in ['Meat', 'Coal', 'Iron'] else ''}"
            for res, val in section.items() if not (res == "Refined Crystal" and val == 0)
        )
        embed.add_field(name=title, value=text, inline=False)
    return embed
  # Ithan
