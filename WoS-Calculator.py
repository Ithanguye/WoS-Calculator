about = """
WoS Resource Calculator Bot
Author: Ithan
""" 
import discord, random, os, asyncio, datetime, pytz, dotenv
from discord.ext import commands
from discord.errors import HTTPException
from datetime import datetime, timedelta
from charts import charts, resource_icons, training_camp_chart, embassy_chart, command_center_chart
from random import randint
from glob import glob

# Server time
now = datetime.now()
severtime = now.strftime("`%Y-%m-%d %H:%M:%S`")
# Get user nick:
def get_user_identity(ctx):
    """
    Returns a formatted string with user's display name and ID.
    """
    user = ctx.author
    name = user.display_name if hasattr(user, "display_name") else user.name
    return user.id, name
# Decapital
def normalize_level(level: str) -> str:
    """ Normalize level input to match keys in furnace_chart """
    return level.upper().replace(" ", "")
# Translate level
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
dotenv.load_dotenv("token.env")
mid = os.getenv("MASTER_ID", "0")
master_id = [int(x) for x in mid.split(',') if x.strip().isdigit()]
ID = 333373276
SDS = int(os.getenv("SDS", "0"))
TOKEN = os.getenv("TOKEN")
ALLOWED_GUILD = [int(i.strip()) for i in os.getenv("ALLOWED_GUILD", "").split(",") if i.strip().isdigit()]
R4 = [int(i.strip()) for i in os.getenv("R4_IDS", "").split(",") if i.strip().isdigit()]
# Helper function to check permission
async def check_permissions(ctx, master_id, SDS):
    if ctx.author.id == master_id:
        await ctx.send(f"As your command, Grand Chief.{ctx.author.display_name}")
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
    for key in sorted_keys[start_index+1:stop_index+1]:
        for resource, value in charts[key].items():
            total[resource] += value

    return total, None

# Embassy logic:
def sum_embassy_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)

    sorted_keys = sorted(embassy_chart.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names. Please check the level."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Did you want to downgrade?"

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index+1:stop_index + 1]:
        for resource, value in embassy_chart[key].items():
            total[resource] += value

    return total, None

# Training camp logic:
def sum_tc_rss(start_level: str, stop_level: str):
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
    for key in sorted_keys[start_index+1:stop_index + 1]:
        for resource, value in training_camp_chart[key].items():
            total[resource] += value

    return total, None

# Command Center logic
def sum_cc_rss(start_level: str, stop_level: str):
    start_level = normalize_level(start_level)
    stop_level = normalize_level(stop_level)

    sorted_keys = sorted(command_center_chart.keys(), key=custom_level_key)

    if start_level not in sorted_keys or stop_level not in sorted_keys:
        return None, "Invalid level names. Please check the level."

    start_index = sorted_keys.index(start_level)
    stop_index = sorted_keys.index(stop_level)

    if start_index > stop_index:
        return None, "Did you want to downgrade?"

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for key in sorted_keys[start_index+1:stop_index + 1]:
        for resource, value in command_center_chart[key].items():
            total[resource] += value

    return total, None

# Custom !help 
class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="WoS Resource Calculator",
            description="**Commands available:**",
            color=discord.Color.teal()
        )
        embed.add_field(name="",value=(
            """`!Camp` — Training Camp RSS requirement
            `!Furnace` — Furnace RSS requirement
            `!Upgrade` — RSS for Furnace + Camps
            `!Embassy`
            `!CC` 
            `!dice`  — rolling dice 3 times for fun
                        
            - !help <command> for details.\n
            **Notes:** Rss = Resources, Meat and Wood need the same amount\n\n"""
        ), inline=False)
        embed.set_footer(text=f"""By #2161 Thain #{ID} !total TOTAL RSS for all buildings.    
                                                """)

        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f"Command: `!{command.name}`",
            description=command.help,
            color=discord.Color.blurple()
        )
        await self.context.send(embed=embed)
# BOT SETUP
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(event_announcer())
bot = commands.Bot(command_prefix="!", intents=intents,  help_command=CustomHelpCommand(),case_insensitive=True)

# About Ithan
ascii_emojis = [        
        "╭(◕‿◕)╯", "┌( ಠ_ಠ)┘", "༼ つ ◕_◕ ༽つ", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", "╚(•⌂•)╝",
    "💾🧠⚙️", "🧠→💥", "🥲💡", "🤖✨", "🧙‍♂️🧪",
    "(╯°□°）╯︵ ┻━┻", "┬─┬ ノ( ゜-゜ノ)", "(¬‿¬)", "(▀̿Ĺ̯▀̿ ̿)", "(ง'̀-'́)ง",
    "ヽ(´▽｀)ノ", "(☞ﾟヮﾟ)☞", "¯\\_(ツ)_/¯", "(ﾉಥ益ಥ）ﾉ﻿ ┻━┻", "ಠ_ಠ",
    "(☞⌐■_■)☞", "(^_^)/", "(¬‿¬ )", "(づ｡◕‿‿◕｡)づ", "ʕ•ᴥ•ʔ",
    "( •_•)>⌐■-■", "(°ロ°)☝", "(° ͜ʖ °)", "（＾_＾）", "ಠ‿ಠ",
    "ლ(╹◡╹ლ)", "｡◕‿◕｡", "ʘ‿ʘ", "눈_눈", "∠( ᐛ 」∠)＿", "（✿ ͡◕ ᴗ◕)つ━━✫・*。"
    ]
@bot.command()
async def aboutme(ctx, date = now.strftime("%m %d")):
    """
    Show the handsome face of the bot developer
    """
    git = 'GitHub: https://github.com/Ithanguye/WoS-Calculator'    
    me = ["Recent graduate, with passion for AWS, 2nd Cloudathon @UH 2023",
        "A passionate by season, a lazy code immoral.", "A dedicated survivor of the Whiteout.",
        "🎓 Graduated from University of Houston in Computer Info Wizardry (a.k.a. CIS). Casted spells in AWS, Jira, and caffeine.",
"💻 Survived Valu-Cleaner and Caotoc Net Cafe—battled hardware goblins, exorcised network demons, and silenced crashing software ghosts.",
"🌩️ Currently chasing Network+ and CCNA scrolls to level up my networking and cloud sorcery.",
"📦 Capstone project? Oh, just summoned AWS resources and tamed Jira tickets like a pro. No big deal.",
"🤝 Volunteered at BPSOS helping people navigate the treacherous lands of paperwork and tech quests.",
          ]
    
    emoji = random.choice(ascii_emojis)
    greetings = ["Hello!", "你好!", "Xin chào!"]
    greet = random.choice(greetings)
    tt = f"{greet}{emoji}"
    album = glob("*.jpeg")
    img = random.choice(album)
    try:
        if ctx.guild.id != 1356157767131599010 and ctx.author.id not in master_id:
            await ctx.send(f"{ctx.author.id} your ID, Master ID: {master_id}\n\nAuthor:{git}")
            return
        file = discord.File(img, filename=img) # file = discord.File(file_path, filename="th.jpg")
        embed = discord.Embed(
            title= (tt),
            description= random.choice(me),
            color=discord.Color.orange()
        )        
        embed.set_image(url=f"attachment://{img}")
        embed.set_footer(text=f"© 2025 {date}\nIthan, Thain, and Thai-Anh\n✨ Powered by interest, GPT, and a bit of chaos.{emoji}")
        await ctx.send(file=file, embed=embed)
    except Exception as e:
        await ctx.send(f"Thain is sleeping...")
        print(e)
# next img        
usage_counter = {}
@bot.command()
async def next(ctx):
    """
    Sends a random image from /photos with a random ASCII emoji.    
    """
    userid, n = get_user_identity(ctx)
    # Count
    uid = int(userid)
    counter = {}
    usage_counter[userid] = counter.get(userid, 0) + 1
    print(usage_counter)
    if usage_counter[userid] >= 2 and uid != master_id:
        await ctx.send("Ấy... hết hình rồi, lần sau nhé")
        print(master_id, userid)
        return
    # Load images from the 'photos' subfolder
    album = glob("photos/*.jpg") + glob("photos/*.jpeg") + glob("photos/*.png")
    if not album:
        print("No photos found in the 'photos' folder.")
        return    
    
    image = random.choice(album)
    emoji = random.choice(ascii_emojis)

    try:
        file = discord.File(image, filename=image.split("/")[-1])
        embed = discord.Embed(description=emoji, color=discord.Color.random())
        embed.set_image(url=f"attachment://{image.split('/')[-1]}")
        await ctx.send(file=file, embed=embed)
    except Exception as e:
        # await ctx.send("Something went wrong showing your handsome self.")
        print(e)

# BOT COMMANDS: 
# Bear Trap announcement
hunt_enabled = True
async def event_announcer():
    await bot.wait_until_ready()
    channel_id = 1330342486081802362  # Replace this with the actual channel ID (int)
    channel = bot.get_channel(channel_id)
    global hunt_enabled

    if not channel:
        print("Channel not found.")
        return

    while not bot.is_closed():
        now = datetime.datetime.now() # pytz.utc for utc
        event_time = [
            (19, 45, "@here Bear trap in 30 minutes"),
            (19, 0, "@here Bear hunt's in 15', prepare you Squad formation"),
            (20, 5, "@everyone Bear hunt's in 10', call your Troops back, prepare for Bear hunting!"),
            (20, 15, "@everyone Bear hunt right now!")
        ]

        for hour, minute, message in event_time:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += datetime.timedelta(days=1)  # schedule for next day

            wait_time = (target - datetime.datetime.now()).total_seconds()

            print(f"⏳ Waiting {wait_time:.2f} seconds for bear hunt message...")
            await asyncio.sleep(wait_time)

            await channel.send(
                content=message,
                allowed_mentions=discord.AllowedMentions(everyone=True)
            )

        await asyncio.sleep(60)  # small sleep buffer after each cycle

@bot.command()  
#  0.0.0.1 !crush
async def crush(ctx, hour: int, minute: int, *, text: str = "It's SHOWTIME!"):
    """
    Schedule an @everyone alert with hero instructions at a specific local time.
    """
    zone = pytz.UTC  # Timezone utc
    now = datetime.now(zone)
    severtime = now.strftime("`%Y-%m-%d` %H:%M:%S")
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target < now:
        target += datetime.timedelta(days=1)

    wait_time = (target - now).total_seconds()
    hours = int(wait_time // 3600)
    minutes = int((wait_time % 3600) // 60)
    seconds = int(wait_time % 60)

    parts = text.split("|")
    event = parts[0].strip()
    bear = (
        "**FIRST hero** for joining must be one of:\n"
        "•  Jessie\n"
        "•  Jasser\n"
        "•  Seo-yoon\n"
        "•  Jeronimo\n"
        "•  Mia\n"
        "• Or send your troops with **NO hero** if none apply\n\n"
        "❗ Sending wrong hero = *release* from rally."
    )
    hint = parts[1].strip() if len(parts) > 1 else bear

    print(f"In: {hours} hours, {minutes} minutes, {seconds} seconds")

    if wait_time > 0:
        await ctx.send(f"*Current server date:*\n{severtime}\nEvent starts in **{hours}:{minutes}:{seconds}**")
    else:
        await ctx.send(f"Announcing Event tomorrow in *{hours}:{minutes}:{seconds}*")

    await asyncio.sleep(wait_time)

    # Send in chosen channel
    channel_id = 1330342044052357282  # channel ID
    announce_channel = ctx.bot.get_channel(channel_id)

    if not announce_channel:
        print("⚠️ No channel.")
        return

    embed = discord.Embed(
        title=f"{event}",
        description=f"{hint}",
        color=discord.Color.red()
    )
    embed.set_footer(text="May the net be with you!")

    # Production version:
    # await announce_channel.send(
    #     content="@everyone",
    #     embed=embed,
    #     allowed_mentions=discord.AllowedMentions(everyone=True)
    # )

    # For testing, sends it to ctx instead
    await ctx.send(
        content="@here",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True)
    )


# Toggle announcement
@bot.command()
async def trap(ctx):
    global hunt_enabled
    hunt_enabled = True
    await ctx.send("🐻 Trap announcements enabled!")

@bot.command()
async def trap_off(ctx):
    global hunt_enabled
    hunt_enabled = False
    await ctx.send("Announcements disabled.")

# !furnace
@bot.command()
async def furnace(ctx, start: str, stop: str):
    """Calculates rss cost for Furnace
    Usage: `!furnace fcX fcY`
    
    With:        
        X: your Furnace level. From 30-1 to FC5
        Use 30-1 for Lv.30, FC for FC, obviously.
        Y: Furnace level you want to reach.
        
        Althought it's possible...I wouldn't encourage you to downgrade (entering X > Y).        
        
    Example: `!furnace 30-1 FC3` rss from Lv.30-1 to FC3
    or
    `!furnace FC1 FC2` rss from FC1 to FC2
    """
    
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
    """Calculates rss cost for a training Camp
    Usage: `!camp fcX fcY`
    
    With:        
        X: your Camp level. From 30-1 to FC5
        Use 30-1 for Lv.30, FC for FC, obviously.
        Y: Camp level you want to reach.                
        
    Example: `!camp 30-1 FC3` rss from Lv.30 to FC3
    or `!camp FC1 FC2` rss from FC1 to FC2
    
    *Note: 
        All camps require the same amount of rss.*        
        *Furnace of same Lv is prereq of all camps.*
    """
    # print(ctx.author.display_name, "used !camp")
    total, error = sum_tc_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)

# !Embassy
@bot.command()
async def embassy(ctx, start: str, stop: str):
    """Calculates rss cost for a training Camp
    Usage: `!embassy fcX fcY`
    
    With:        
        X: your Embassy level. From 30-1 to FC5
        Use 30-1 for Lv.30, FC for FC, obviously.
        Y: Embassy level you want to reach.                
    """
    # print(ctx.author.display_name, "check !Embassy")        
    total, error = sum_embassy_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)    

# !CC
@bot.command()
async def CC(ctx, start: str, stop: str):
    # print(ctx.author.display_name, "used CC")
    # await ctx.send("In develop, Frost Star will make it pop~")
    # return
    total, error = sum_cc_rss(start, stop)
    if error:
        await ctx.send(error)
        return
    user = ctx.author.display_name
    output = embed_msg(start, stop, total, user)
    await ctx.send(embed=output)
# OUTPUT

colors = [
        discord.Color.orange(),
        discord.Color.blue(),
        discord.Color.og_blurple(),
        discord.Color.purple(),
        discord.Color.gold(),
        discord.Color.teal(),
        discord.Color.red()    ]
# Embeded msg
def embed_msg(start: str, stop: str, total: dict, user = None) -> discord.Embed:    
    # Returns a Discord embed displaying furnace resource totals.    
    embed = discord.Embed(
        title=f"`{user}`'s Resource Summary",
        description=f"**From `{start}` to `{stop}`**",        
        color=random.choice(colors)
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
    """    Calculates total Furnace + 3 Training Camps resources with optional discount.
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
    # print(ctx.author.display_name, "used !upgrade")
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
        camp_total, c_err = sum_tc_rss(start_level, stop_level)
        embs_total, em_err = sum_embassy_rss(start_level, stop_level)
        cc_total, cc_err = sum_cc_rss(start_level, stop_level)

        if f_err or c_err or em_err or cc_err:
            await ctx.send(f"Furnace error: {f_err or 'OK'}\nCamp error: {c_err or 'OK'}")
            # print(cc_err, em_err)
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
        emb_dc = apply_discount(embs_total)
        cc = apply_discount(cc_total)
        total = {k: furnace_discounted.get(k, 0) + camp_discounted.get(k, 0) + emb_dc.get(k, 0) for k in set(furnace_total)}

        # Output Embed
        embed = discord.Embed(
            title="Total Upgrade Cost",
            description=f"**Furnace + Camps** from `{start_level}` to `{stop_level}`",
            color=discord.Color.red()
        )
        embed.add_field(name="Furnace", value=format_resource_lines(furnace_discounted), inline=False)
        embed.add_field(name="Training Camps", value=format_resource_lines(camp_discounted), inline=False)
        embed.add_field(name="Embassy", value=format_resource_lines(emb_dc), inline=False)
        embed.add_field(name="Total", value=format_resource_lines(total), inline=False)
        embed.set_footer(text=f"Discount applied: {reduction}%" if reduction else f"{ctx.author.display_name}, Happy hoarding~")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Usage: `!upgrade fc1-fc5`")
        print(e)

# !about
async def get_sponsor_name(user_id, guild=None):
    """
    Returns the display name (nickname if in guild, else username).
    """
    # If in a server
    if guild:
        member = guild.get_member(user_id)
        if member:
            return member.nick or member.name
        try:
            member = await guild.fetch_member(user_id)
            return member.nick or member.name
        except discord.NotFound:
            pass  # Not in server

    # Fallback: global username
    try:
        user = await bot.fetch_user(user_id)
        return user.name
    except:
        return str(user_id)

import random

@bot.command()
async def sds(ctx): # !about
    guild = ctx.guild if ctx.guild else None
    album = glob("*.jpg")
    img = random.choice(album)
         
    crush_name = "Crush"  # await get_sponsor_name(crushid, guild)
    fluffy_name = "Fluffy"  # await get_sponsor_name(fluffyid, guild)
    lipton_name = "Lippy"  # await get_sponsor_name(lippyid, guild)

    crush_lines = [
        f"At the suggestion of our dear **{crush_name}** — the all-knowing, slightly chaotic *HiJ* Master of SDS.",
        f"Suggested (and totally not forced) by **{crush_name}**, HiJ, overlord of SDS and occasional whale summoner.",
        f"Brought to you under the divine whisper of **{crush_name}**, HiJ Master of SDS."
    ]

    crush_pirate_lines = [        
        f"Commissioned by **{crush_name}**, dread pirate of SDS, who sails the frozen wastelands in search of Fire Crystal... and snacks."        
    ]

    lippy_lines = [
        f"Inspired by the wise and sometimes suspiciously quiet **{lipton_name}**."        
    ]

    fluffy_lines = [
        f"Requested by the almighty cat-lover **{fluffy_name}**, meow-powered and unstoppable.",
        f"Because **{fluffy_name}** asked — and let’s face it, no one says no to cats.",        
    ]

    footers = [
        "All rights reserved. Because Crush said so. And let’s be honest, nobody wants to deal with his “Dude, we need to talk” DMs. 🙃 - Jenily",
        "All rights reserved by decree of Crush the Eternal Ex-President, HiJ Master of SDS, Slayer of Beasts, and Bear Hunt's non-stop Whisperer. Any unauthorized use shall summon the full wrath of his keyboard and a rain of sarcastic GIFs from which none shall escape. Tread carefully, Chief... for the ex-President's gaze sees all.",
        "Touch this bot without permission, and Copper'll turn your meat into coal and your wood into a mound of soft regret.",
        "All rights reserved — or Page'll burn your wood, break your iron, and mince your meat :dagger: - By Sera's order",
        "Unauthorized use will result in your coal being stolen and your wood... prematurely exhausted. Because Page said so",
        "Keep your iron hard, your coal hot, and your wood ready — but this code? Off limits - Tony",
        "By the frozen flag of SDS, Cap’n Crush claims this code - DRU",
        "Violate this bot and thee shall face consequence of overtaint - Lord Undertaint"
            ]

    # Randomly decide whether to use pirate or regular HiJ Master tone
    chosen_crush_line = random.choice(crush_lines + crush_pirate_lines)
    file = discord.File(img, filename=img)
    embed = discord.Embed(
        title="WoS Calculator",
        description=(
            "Resource calculator for Server #2161\n\n"
            f"{chosen_crush_line}\n"
            f"{random.choice(lippy_lines)}\n"
            f"{random.choice(fluffy_lines)}\n"
            "\nNot for *kids*, nor *geniuses*.\n\n"
            "**© 2025 Thain.**"
        ),
        color=discord.Color.orange()
    )
    embed.set_image(url=f"attachment://{img}")
    embed.set_footer(text=random.choice(footers))
    await ctx.send(file=file, embed=embed)
    #await ctx.send(embed=embed)

# Clear mesg !cl
@bot.command(hidden=True)
async def cl(ctx, mcount: int = 5):
    messages = [m async for m in ctx.channel.history(limit=50)]
    bot_msgs = [m for m in messages if m.author == bot.user][:mcount]
    user_msg = []
    if ctx.guild: # Check if DM
        bot_mem = ctx.guild.get_member(bot.user.id)
        if bot_mem.guild_permissions.manage_messages:
            user_msg = [m for m in messages if m.author == ctx.author][:mcount]    
    # Combine both lists to delete
    msgs = user_msg + bot_msgs
    # Delete    
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
    await ctx.send(f"Deleted {deleted} messages!", delete_after = 10)

@bot.command()
async def clr(ctx, mcount: int = 10):
    messages = [m async for m in ctx.channel.history(limit=50)]    
    user_msg = [m for m in messages if m.author == ctx.author][:mcount]
    Del = 0
    for d in user_msg:
        try:            
            await d.delete()
            Del += 1
            await asyncio.sleep(1)
        except HTTPException as e:
            print(e)
    await ctx.send(f"Self deleted {Del}", delete_after = 3)    
    
# Handling unknown command
@bot.event
async def on_command_error(ctx, error):
    from discord import Embed
    import random
    
    userid, usernick = get_user_identity(ctx)
    embed = Embed(title=f"Oops! {usernick} did it again~", color=random.choice(colors))

    if isinstance(error, commands.CommandNotFound):
        print(f"{userid}, {error}")
        embed.description = f"Dear **{usernick}**,"
    elif isinstance(error, commands.MissingRequiredArgument):
        embed.description = "You didn’t enter a level, don’t you even know what you want? :eyes:"
    elif isinstance(error, commands.BadArgument):
        embed.description = "One of your level inputs is invalid."
    elif isinstance(error, commands.MissingPermissions):
        embed.description = "This is for VIPs only~"
    else:        
        raise error

    embed.set_footer(text="Try `!help` if you're lost.")
    await ctx.send(embed=embed)
    
# For fun
@bot.command(hidden=True)
async def dice(ctx, number: int = 6, min: int = 1):
    dice = number
    result = randint(min, dice)
    player = ctx.author.display_name
    userid, unick = get_user_identity(ctx)
    # Count
    
    usage_counter[userid] = usage_counter.get(userid, 0) + 1

    if usage_counter[userid] >= 3 and userid not in master_id:
        await ctx.send(f"Dear {unick}, it is time you accept your roll, better luck tomorrow~")        
        return

    # Send the result back to the user
    # if ctx.author.id == 1338528586583379971: # target ID
    #     result = random.randint(-1,3)
    if dice <= 6:
        await ctx.send(f"🎲 **{result}**")            
        if result == dice:            
            await ctx.send(f"**{player}**, nice roll~ :tada:")
    else:        
        result = randint(-dice, dice) if min == 1 else randint(min, dice)
        await ctx.send(f"**{player}**, you got number: **{result}**")
        if result in [16, 7, 12, 11, 84, 2161]:
            await ctx.send(f"Congratulation! It's your lucky number today!:tada:")
        elif result in [-1, -999, -9999]:
            await ctx.send(f"Fantastic! **{player}**, you hit a jackpot: **{result}**")
async def setup_hook():
    await bot.load_extension("slash_total_command")  # or use full path if nested

# bot.setup_hook = setup_hook

# Start bot, uncomment to show time
@bot.event
async def on_ready():
    utc = pytz.UTC
    now = datetime.now(utc)
    svt = now.strftime("%m-%d %H:%M")
    
    channel = bot.get_channel(1359358885433180170)
    hour = now.hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    greetings = f"{greeting} Chief, I'm now at your command!\n`Current Server Time: {svt}`"
    await channel.send(greetings)
    print("Master ID:",master_id)
    # print(greetings)


@bot.command()
async def total(ctx, range_str: str, percent: str = "0", cc: str = ""):
    """
    Calculates total Furnace + Camp x3 + Embassy + optional CC
    Usage: 
    `!total FCX-FCY`
    `!total FCX-FCY 15 cc`
    
    Same usage as Upgrade with optional cc for Command Center
    """
    if ctx.author.id not in master_id:
        await ctx.send("In develop, Frost Star will make it pop~")
        return
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

        furnace_total, f_err = sum_furnace_rss(start_level, stop_level)
        camp_total, c_err = sum_tc_rss(start_level, stop_level)
        embs_total, em_err = sum_embassy_rss(start_level, stop_level)
        cc_total, cc_err = (sum_cc_rss(start_level, stop_level) if cc.lower() == "cc" else ({"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}, None))

        if f_err or c_err or em_err or (cc and cc_err):
            await ctx.send(f"Furnace: {f_err or 'OK'}, Camp: {c_err or 'OK'}, Embassy: {em_err or 'OK'}, CC: {cc_err or 'OK'}")
            return

        def apply_discount(rss):
            discounted = {}
            for res, val in rss.items():
                if res in ["Meat", "Coal", "Iron"]:
                    val *= (1 - reduction / 100)
                discounted[res] = round(val)
            return discounted

        furnace_discounted = apply_discount(furnace_total)
        camp_discounted = apply_discount({k: v * 3 for k, v in camp_total.items()})
        emb_dc = apply_discount(embs_total)
        cc_dc = apply_discount(cc_total)

        total = {k: furnace_discounted.get(k, 0) + camp_discounted.get(k, 0) + emb_dc.get(k, 0) + cc_dc.get(k, 0) for k in furnace_total}

        embed = discord.Embed(
            title="Total Upgrade Cost",
            description=f"**Furnace + Camps + Embassy{' + CC' if cc else ''}** from `{start_level}` to `{stop_level}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Furnace", value=format_resource_lines(furnace_discounted), inline=False)
        embed.add_field(name="Training Camps", value=format_resource_lines(camp_discounted), inline=False)
        embed.add_field(name="Embassy", value=format_resource_lines(emb_dc), inline=False)
        if cc:
            embed.add_field(name="Command Center", value=format_resource_lines(cc_dc), inline=False)
        embed.add_field(name="Total", value=format_resource_lines(total), inline=False)
        embed.set_footer(text=f"Discount applied: {reduction}%")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Usage: `!total fc1-fc5 15 cc` — {e}")
bot.run(TOKEN)


# 🔄 Unified building RSS calculator
def sum_building_rss(start, stop, chart):
    try:
        start = int(start)
        stop = int(stop)
        if start > stop:
            return None, "Invalid range: start must be <= stop"
    except ValueError:
        return None, "Start and stop must be integers"

    total = {"Meat": 0, "Coal": 0, "Iron": 0, "Fire Crystal": 0, "Refined Crystal": 0}
    for level in range(start, stop):
        key = "F 30" if level == 0 else f"FC {level}"
        if key in chart:
            for res, val in chart[key].items():
                total[res] += val * 5
    return total, None

# Centralized embed message formatter
def embed_msg(start, stop, total_rss, nickname, building="Upgrade Summary"):
    import discord
    embed = discord.Embed(
        title=f"{building}",
        description=f"From FC {start} → FC {stop}",
        color=discord.Color.orange()
    )

    embed.add_field(name="Resources", value=(
        f"**Meat**: {total_rss['Meat']}M\n"
        f"**Wood**: {total_rss['Meat']}M\n"
        f"**Coal**: {total_rss['Coal']}M\n"
        f"**Iron**: {total_rss['Iron']}M\n"
        f"**Fire Crystal**: {total_rss['Fire Crystal']}\n"
        f"**Refined FC**: {total_rss['Refined Crystal']}"
    ), inline=False)

    embed.set_footer(text=f"Requested by {nickname}")
    return embed

# 🔁 Dispatcher for all building commands
async def send_building_summary(ctx, building_name, start, stop, chart):
    total, error = sum_building_rss(start, stop, chart)
    if error:
        await ctx.send(f"❌ {error}")
        return
    output = embed_msg(start, stop, total, ctx.author.display_name, building=building_name)
    await ctx.send(embed=output)
