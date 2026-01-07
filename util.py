import discord, datetime, calendar, requests, logging

from discord.ext import commands, bridge

from functools import wraps

from functools import wraps

from .tracking import databases

from .config import CONFIG, both_in, guild_in


def selfArgument(func):
  @wraps(func)
  async def wrapped(self, ctx, *args, **kwargs):
    if kwargs["username"] is None:
      uuid = get_mapped_account(ctx.author)

      kwargs["username"] = uuid

    return await func(self, ctx, **kwargs)

  return wrapped

async def fail_tracking_required(self, ctx, *args, **kwargs):
  await ctx.respond("Tracking must be enabled to use this command.")
  return

def trackingRequired(func):
  @wraps(func)
  async def wrapped(self, ctx, *args, **kwargs):
    if not getattr(CONFIG, "TRACKING_ENABLED", False):  # safer than direct access
      return await fail_tracking_required(self, ctx, *args, **kwargs)
    return await func(self, ctx, *args, **kwargs)
  
  return wrapped
      

directory = None

class Util(commands.Cog):
  def __init__(self, dir):
    global directory
    directory = dir

  @commands.Cog.listener()
  async def on_ready(self):
    logging.info("Initializing databases.")
    await databases.initialize_dbs(directory)

  @commands.slash_command(integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  async def map_username(self, ctx, minecraft_username):
    uuid = getUUID(minecraft_username)

    if uuid is None:
      await ctx.reply(f"There was an error getting the UUID for {minecraft_username}. Are you sure you typed it correctly?")

    if map_account(ctx.message.author, uuid):
      await ctx.reply("Successfully mapped account.")
    else:
      await ctx.reply("You already have a mapped account.") 



def getUUID(username):
  """
  Gets the UUID of a Minecraft user. If the username is already a UUID, it returns the UUID.
  """

  if(len(username) == 32):
    return username

  try:
    d = datetime.datetime.now()
    timestamp = calendar.timegm(d.utctimetuple())

    url = "https://api.mojang.com/users/profiles/minecraft/{0}?at={1}".format(username, timestamp)
    data = requests.get(url).json()
    return data["id"]
  except Exception as e:
    logging.error(e)
    logging.error(f"Error while getting uuid for {username}.")
    return None
	
def get_mapped_account(user: discord.User):
  with open(directory + "/data/mappedusernames.csv", 'r') as f:
    lines = f.readlines()

    lines = dict([line.strip().split(",") for line in lines])

    id = str(user.id)

    if id in lines:
      return lines[id]
    else:
      print("user not in lines")
      logging.info(f"User {user.global_name} has not mapped their account.")
      return None


def map_account(user: discord.User, uuid):
  if get_mapped_account(user) is not None:
    logging.info(f"{user.global_name} has already mapped their account. Ignoring.")
    return False

  with open(directory + "/data/mappedusernames.csv", 'a') as f:
    f.write(f"{user.id},{uuid}\n")
    return True

# TODO write unmap account

def wins_to_prestige(wins):
  """Returns a tuple of prestige and the number of wins needed to reach it. For some modes, required wins have been halved and wins_to_prestige_havled should be used instead/"""
  for wins_needed, prestige in prestiges:
    wins_needed = wins_needed

    if wins_needed > wins:
      return (prestige, wins_needed-wins)
  
  return ("MAX PRESTIGE", 0)

def wins_to_prestige_halved(wins):
  """Returns a tuple of prestige and the number of wins needed to reach it where required wins have been halved (e.g. bridge, parkour)."""
  for prestige, wins_needed in prestiges:
    wins_needed = int(wins_needed/2)

    if wins_needed > wins:
      return (prestige, wins_needed-wins)
  
  return ("MAX PRESTIGE", 0)
    
def get_prestige(wins):
  """Returns the prestige of a player based on their wins. For some modes, required wins have been halved and get_prestige_halved should be used instead."""
  last = "N/A"

  for prestige, wins_needed in prestiges:
    if wins < wins_needed:
      break

    last = prestige

  return last

def get_prestige_halved(wins):
  """For duelmodes where required wins have been halved (e.g. bridge, parkour)"""
  last = "N/A"
  for prestige, wins_needed in prestiges:
    if wins < int(wins_needed/2):
      break

    last = prestige
  
  return last


prestiges = [
        ("Rookie", 50),
        ("Rookie II", 60),
        ("Rookie III", 70),
        ("Rookie IV", 80),
        ("Rookie V", 90),
        ("Iron", 100),
        ("Iron II", 130),
        ("Iron III", 160),
        ("Iron IV", 190),
        ("Iron V", 220),
        ("Gold", 250),
        ("Gold II", 300),
        ("Gold III", 350),
        ("Gold IV", 400),
        ("Gold V", 450),
        ("Diamond", 500),
        ("Diamond II", 600),
        ("Diamond III", 700),
        ("Diamond IV", 800),
        ("Diamond V", 900),
        ("Master", 1000),
        ("Master II", 1200),
        ("Master III", 1400),
        ("Master IV", 1600),
        ("Master V", 1800),
        ("Legend", 2000),
        ("Legend II", 2600),
        ("Legend III", 3200),
        ("Legend IV", 3800),
        ("Legend V", 4400),
        ("Grandmaster", 5000),
        ("Grandmaster II", 6000),
        ("Grandmaster III", 7000),
        ("Grandmaster IV", 8000),
        ("Grandmaster V", 9000),
        ("Godlike", 10000),
        ("Godlike II", 12000),
        ("Godlike III", 14000),
        ("Godlike IV", 16000),
        ("Godlike V", 18000),
        ("Celestial", 25000),
        ("Celestial II", 30000),
        ("Celestial III", 35000),
        ("Celestial IV", 40000),
        ("Celestial V", 45000),
        ("Divine", 50000),
        ("Divine II", 60000),
        ("Divine III", 70000),
        ("Divine IV", 80000),
        ("Divine V", 90000),
        ("Ascended", 100000),
    ]