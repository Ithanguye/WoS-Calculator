about = """
WoS Resource Calculator Bot
Author: Ithan
""" 
import discord
from discord.ext import commands
from charts import charts, resource_icons, training_camp_chart
import asyncio
from discord.errors import HTTPException

def normalize_level(level: str) -> str:
    """ Normalize level input to match keys in furnace_chart """
    return level.upper().replace(" ", "")

def custom_level_key(level: str):
    if level.startswith("30-"):
        try:
            sub = int(level.split("-")[1])
        except:
            sub = 0
        return (0, sub)
    elif level.startswith("FC"):
        rem = level[2:]
        if "-" in rem:
            parts = rem.split("-")
            try:
                main = int(parts[0])
            except:
                main = 0
            try:
                sub = int(parts[1])
            except:
                sub = 0
        else:
            try:
                main = int(rem)
            except:
                main = 0
            sub = 0
        return (1, main, sub)
    else:
        return (2, level)
# Check permission
# Thain
master_id = os.getenv(master_id)
ID = 123 # game ID
# SDS:
R4 = 123 # roles
SDS = 133 # guilds

# Helper function to check permission
async def check_permissions(ctx, master_id, SDS):
    if ctx.author.id == master_id:
        await ctx.send("As your command, Grand Chief.")
        return True    
        
    if ctx.guild is None:        
        if ctx.author.id == R4:
            #await ctx.send(f"{ctx.author.nick}.")
            return True
        else: 
            await ctx.send("Who're you?")
            return False           
    #print(f"User's ID: {ctx.author.id}, Master ID: {master_id}")
    
    # Check for specific guild        
    if ctx.guild.id == 1335426899635343381: # Usable in SvS
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            print(f"Alliance: {ctx.guild.id}, allowed alliance: {SDS}")
            await ctx.send("Dear **heretic**, please, go away!")
            return False
# Furnace calculation logic
def sum_furnace_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)
    
    sorted_keys = sorted(charts.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Are you trying to downgrade? Whack yourself in the face is all it takes..."

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index:stop_index+1]:
        for resource, value in charts[key].items():
            total[resource] += value

    return total, None

# Training camp calc:
def sum_camp_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)

    sorted_keys = sorted(training_camp_chart.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names. Please check your input."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Start level must come before stop level."

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index:stop_index + 1]:
        for resource, value in training_camp_chart[key].items():
            total[resource] += value

    return total, None

# Custom help 
class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="WoS Resource Calculator",
            description="These are the commands currently available:",
            color=discord.Color.teal()
        )
        embed.add_field(name="Commands", value=(
            "`!Camp` — Training Camp RSS (Infantry/Lancer/MM)\n"
            "`!Furnace` — Furnace upgrade RSS\n"
            "`!Upgrade` — Total RSS for Furnace + Camps\n"
            "`!Embassy` — implementing~\n"
            "`!CC` — *Coming soon...*"
        ), inline=False)
        embed.set_footer(text="Use !help <command> for detailed info.\nRss = Resources")

        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f"ℹ️ Help: {command.name}",
            description=command.help,
            color=discord.Color.blue()
        )
        await self.context.send(embed=embed)
# BOT SETUP
intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix="!", intents=intents,  help_command=CustomHelpCommand(),case_insensitive=True)

# BOT COMMANDS: 
# !furnace
@bot.command()
async def furnace(ctx, start: str, stop: str): # change furnace to command of your choice
    """calculates rss cost for Furnace
    Usage: `!furnace fcX fcY`
    
    With:        
        X: your Furnace level. From 30-1 to FC5
        Use 30-1 for Lv.30, FC for FC, obviously.
        Y: Furnace level you want to reach.
        Althought it's possible...I wouldn't encourage you to downgrade(entering X > Y).
        
        
    Example: `!furnace 30-1 FC3` rss from Lv.30 to FC3
    or `!furnace FC1 FC2` rss from FC1 to FC2
    """
    print(ctx.author.display_name, "used !furnace")
    total, error = sum_furnace_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)

# !camp    
@bot.command()
async def camp(ctx, start: str, stop: str):
    """calculates rss cost for a training Camp
    Usage: `!camp fcX fcY`
    
    With:        
        X: your Camp level. From 30-1 to FC5
        Use 30-1 for Lv.30, FC for FC, obviously.
        Y: Camp level you want to reach.                
        
    Example: `!camp 30-1 FC3` rss from Lv.30 to FC3
    or `!camp FC1 FC2` rss from FC1 to FC2
    
    *Note: 
        All camps require the same quatity of rss.*
        If you reached Lv.30 without knowing this:
        *You need to upgrade the Furnace first before upgrading camps of same Lv.*
    """
    print(ctx.author.display_name, "used !camp")
    total, error = sum_camp_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)

# !Embassy
@bot.command()
async def embassy(ctx, start: str, stop: str):
    print(ctx.author.display_name, "used implementing")    
    if ctx.author.id == master_id:
        total, error = sum_camp_rss(start, stop)
        if error:
            await ctx.send(error)
            return
        user = ctx.author.display_name
        output = embed_msg(start, stop, total, user)
        await ctx.send(embed=output)
    await ctx.send("In develop, Frost Star will make it pop~")

# !CC
@bot.command()
async def cc(ctx, start: str, stop: str):
    print(ctx.author.display_name, "used implementing")
    await ctx.send("In develop, Frost Star will make it pop~")
    return
    total, error = sum_camp_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)
# OUTPUT
# Embeded msg
def embed_msg(start: str, stop: str, total: dict, user = None) -> discord.Embed:    
    # Returns a Discord embed displaying furnace resource totals.    
    embed = discord.Embed(
        title=f"`{user}'s` Resource Summary",
        description=f"**From `{start}` to `{stop}`**",
        color=discord.Color.orange()
    )    

    lines = []
    for resource in ["Meat", "Coal", "Iron", "Fire Crystal", "Refined Crystal"]:
        amount = total.get(resource, 0)
        if resource == "Refined Crystal" and amount == 0:
            continue  # Skip RFC if 0
        if amount > 0:
            amount = round(amount, 1)

        emoji = resource_icons.get(resource, "")
        suffix = "M" if resource in ["Meat", "Coal", "Iron"] else ""
        lines.append(f"{emoji} **{resource}**: {amount}{suffix}")

    embed.add_field(name="Resources", value="\n".join(lines), inline=False)
    if user:
        embed.set_footer(text="Happy hoarding~")

    return embed

# Format for upgrade command
def format_resource_lines(resource_dict, label="", use_icons=True):
    lines = []
    for resource, value in resource_dict.items():
        if resource == "Refined Crystal" and value == 0:
            continue
        emoji = resource_icons.get(resource, "") if use_icons else ""
        suffix = "M" if resource in ["Meat", "Coal", "Iron"] else ""
        lines.append(f"{emoji} **{resource}**: {round(value, 1)}{suffix}")
    return "\n".join(lines)

# !upgrade range-range percent(optional)
@bot.command()
async def upgrade(ctx, range_str: str, percent: str = "0"):
    """
    Calculates total Furnace + 3 Training Camps resources with optional discount.
    Usage: `!upgrade FCX-FCY Z`
    
    X, Y, Z is the numbers with:
        X: Current Furnace's level. Use FC for level 30.
        Y: Your target/desire level
        Z: optional, check your Zinman's Bastionist -mid right- skill for percent(3 - 15%)
    Leave it alone if you don't know what it is.
    **Example:**
    `!upgrade FC1-FC3` -> Total rss from Fire Crystal 1 to 3
    `!upgrade FC-FC3 15` -> Total rss from Lvl 30 to FC 3 with 15% discount.
    **This DOESN'T cover Embassy and CC cost.**
    
    """
    print(ctx.author.display_name, "used !upgrade")
    try:
        def normalize_input(level_str):
            level_str = level_str.lower()
            if level_str == "fc":
                return "30-1"
            elif level_str.startswith("fc") and level_str[2:].isdigit():
                return f"FC{level_str[2:]}"
            return level_str.upper()

        # Parse input
        start_str, stop_str = range_str.split("-")
        start_level = normalize_input(start_str)
        stop_level = normalize_input(stop_str)

        reduction = int(percent)
        if reduction not in range(0, 16):
            await ctx.send("Bastionist max is 15% (Zinman's mid right skill)")
            return

        # Get resource totals
        furnace_total, f_err = sum_furnace_rss(start_level, stop_level)
        camp_total, c_err = sum_camp_rss(start_level, stop_level)

        if f_err or c_err:
            await ctx.send(f"Furnace error: {f_err or 'OK'}\nCamp error: {c_err or 'OK'}")
            return

        # Apply discount to eligible resources
        def apply_discount(rss):
            discounted = {}
            for res, val in rss.items():
                if res in ["Meat", "Coal", "Iron"]:
                    val *= (1 - reduction / 100)
                discounted[res] = round(val)
            return discounted

        furnace_discounted = apply_discount(furnace_total)
        camp_discounted = apply_discount({k: v * 3 for k, v in camp_total.items()})
        total = {k: furnace_discounted.get(k, 0) + camp_discounted.get(k, 0) for k in set(furnace_total)}

        # Output Embed
        embed = discord.Embed(
            title="Total Upgrade Cost",
            description=f"**Furnace + Camps** from `{start_level}` to `{stop_level}`",
            color=discord.Color.red()
        )
        embed.add_field(name="Furnace", value=format_resource_lines(furnace_discounted), inline=False)
        embed.add_field(name="Training Camps", value=format_resource_lines(camp_discounted), inline=False)
        embed.add_field(name="Total", value=format_resource_lines(total), inline=False)
        embed.set_footer(text=f"Discount applied: {reduction}%" if reduction else f"{ctx.author.display_name}, Happy hoarding~")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Error: {e} — Usage: `!upgrade fc1-fc5`")

# About !info
@bot.command()
async def info(ctx):
    inf = """Resources calculator for WoS #2161
    Suggested and inspired by Crush the over(estimated)-Chief-lord.
    As Fluffy
    Used for SvS, not meant for *too* young adults, nor geniuses.
    By **Thain**
    """
    await ctx.send(inf)
# Clear mesg !cl
@bot.command(hidden=True)
async def cl(ctx, mcount: int = 5):
    messages = [m async for m in ctx.channel.history(limit=50)]
    bot_msgs = [m for m in messages if m.author == bot.user][:mcount]
    umsgs = [msg for msg in messages if msg.author == ctx.author][:mcount]
    # Combine both lists to delete
    msgs = umsgs + bot_msgs
    # Delete
    # u_nick = ctx.author.nick if ctx.author.nick else ctx.author.name
    deleted = 0
    for m in msgs:
        try:
            await m.delete()
            deleted += 1
            await asyncio.sleep(0.5)
        except HTTPException as e:
            if e.status == 429:
                print("Rate limited!")
                break
            else:
                print(f"Delete error: {e}")
    print(f"Deleted {deleted} messages!")
    
# Get user nick:
def get_user_identity(ctx):
    """
    Returns a formatted string with user's display name and ID.
    """
    user = ctx.author
    name = user.display_name if hasattr(user, "display_name") else user.name
    return user.id, name
# For unknown command
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # 
        userid, nick = get_user_identity(ctx)
        print(f"{userid}, {error}")
        await ctx.send(f"Did you call me, **{nick}**? ")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You didnn't enter a level, don't you even know you what you want? :eyes:")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("One of your level is invalid.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Who're you? This service is reserved for my donators~")
    else:
        print("Error")
        raise error  # re-raise other errors so you can see them in dev
    await ctx.send("Try `!help` for help.")

@bot.command()
async def credit(ctx):
    await ctx.send(f"Created by Thain, by Krushinit request. \nGitHub: https://github.com/Ithanguye/WoS-Calculator")


# Start bot
TOKEN =  123 # Bot Token
bot.run(TOKEN)
