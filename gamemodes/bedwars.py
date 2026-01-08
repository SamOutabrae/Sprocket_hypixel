import discord
from discord.ext import commands, bridge
from ..config import CONFIG, both_in, guild_in

import logging, requests, datetime
from .. import util 
from dateutil import parser

from ..tracking import tracking, databases

from typing import Optional

def parse_from_json(json):
  """Creates a BedwarsStats object from a JSON response from the Hypixel API."""

  winstreak = "N/A"
  
  try:
      winstreak = json["player"]["stats"]["Bedwars"]["winstreak"]
  except:
      pass

  kills        = json["player"]["stats"]["Bedwars"]["kills_bedwars"]
  deaths       = json["player"]["stats"]["Bedwars"]["deaths_bedwars"]
  voidDeaths   = json["player"]["stats"]["Bedwars"]["void_deaths_bedwars"]
  finalDeaths  = json["player"]["stats"]["Bedwars"]["final_deaths_bedwars"]
  finalKills   = json["player"]["stats"]["Bedwars"]["final_kills_bedwars"]
  bedwarsLevel = json["player"]["achievements"]["bedwars_level"]
  displayname  = json["player"]["displayname"]
  gamesplayed  = json["player"]["stats"]["Bedwars"]["games_played_bedwars"]
  wins         = json["player"]["stats"]["Bedwars"]["wins_bedwars"]
  losses       = json["player"]["stats"]["Bedwars"]["losses_bedwars"]
  kdr          = finalKills/finalDeaths

  stats = BedwarsStats(winstreak, kills, deaths, voidDeaths, finalDeaths, finalKills, bedwarsLevel, gamesplayed, wins, losses, kdr, displayname)
  return stats


class BedwarsStats():
  def __init__(self, winstreak, kills, deaths, voidDeaths, finalDeaths, finalKills, bedwarsLevel, gamesplayed, wins, losses, kdr, displayname):
    self.winstreak    = winstreak
    self.kills        = kills
    self.deaths       = deaths 
    self.voidDeaths   = voidDeaths
    self.finalKills   = finalKills
    self.finalDeaths  = finalDeaths
    self.bedwarsLevel = bedwarsLevel
    self.gamesplayed  = gamesplayed
    self.wins         = wins
    self.losses       = losses
    self.kdr          = kdr
    self.displayname  = displayname

    self.lastResponse = None
  
  @staticmethod
  def get(key: str, uuid=None, username=None):
    if uuid is None and username is not None:
      uuid = util.getUUID(username)
    
    response = None
    url = f'https://api.hypixel.net/player?key={key}&uuid={uuid}'
    try:
      logging.debug(f"Making web request to {url}")
      response = requests.get(url)

      return parse_from_json(response.json())
    except Exception as e:
      logging.error(f"Error while making request to {url}. Response code: {response.status_code}.")
      raise e

  def __add__(self, other):
    killsfinal        = self.kills + other.kills
    deathsfinal       = self.deaths + other.deaths
    voidDeathsfinal   = self.voidDeaths + other.voidDeaths
    finalDeathsfinal  = self.finalDeaths + other.finalDeaths
    finalKillsfinal   = self.finalKills + other.finalKills
    bedwarsLevelfinal = self.bedwarsLevel + other.bedwarsLevel
    gamesplayedfinal  = self.gamesplayed + other.gamesplayed
    winsfinal         = self.wins + other.wins
    lossesfinal       = self.losses + other.losses
    kdrfinal          = self.kdr + other.kdr

    return BedwarsStats(self.winstreak, killsfinal, deathsfinal, voidDeathsfinal, finalDeathsfinal, finalKillsfinal, bedwarsLevelfinal, gamesplayedfinal, winsfinal, lossesfinal, kdrfinal, self.displayname)

  def __sub__(self, other):
    killsfinal        = self.kills - other.kills
    deathsfinal       = self.deaths - other.deaths
    voidDeathsfinal   = self.voidDeaths - other.voidDeaths
    finalDeathsfinal  = self.finalDeaths - other.finalDeaths
    finalKillsfinal   = self.finalKills - other.finalKills
    bedwarsLevelfinal = self.bedwarsLevel - other.bedwarsLevel
    gamesplayedfinal  = self.gamesplayed - other.gamesplayed
    winsfinal         = self.wins - other.wins
    lossesfinal       = self.losses - other.losses

    kdrfinal = 0
    try:
        kdrfinal = finalKillsfinal/finalDeathsfinal
    except:
        pass

    return BedwarsStats(self.winstreak, killsfinal, deathsfinal, voidDeathsfinal, finalDeathsfinal, finalKillsfinal, bedwarsLevelfinal, gamesplayedfinal, winsfinal, lossesfinal, kdrfinal, self.displayname)

  def to_embed_dict(self):
    winloss = 0
    if self.losses + self.wins != 0:
      winloss = self.wins/(self.wins + self.losses)
      pass

    embed_dict = {
      "Level": f"{self.bedwarsLevel}",
      "Winstreak": f"{self.winstreak}",
      "Games played": f"{self.gamesplayed}",
      "Wins": f"{self.wins}",
      "Losses": f"{self.losses}",
      "Win Rate": f"{round(winloss*100)}%",
      "Kills": f"{self.kills}",
      "Deaths": f"{self.deaths}",
      "Void Deaths": f"{self.voidDeaths}",
      "Final Kills": f"{self.finalKills}",
      "Final K/D Ratio": f"{round(self.kdr, 2)}"
    }

    return embed_dict
  
  def to_embed(self, embed=None):
    if embed is None:
      embed = discord.Embed(title = self.displayname, description = "Bedwars stats for " + self.displayname, color=0x00ff00 )

    d = self.to_embed_dict()
    for key in d.keys():
      value = d[key]
      embed.add_field(name = key, value = value, inline = False)
    return embed
  
  def to_date_embed(self, date: datetime.datetime, embed: discord.Embed = None):
    if embed is None:
      embed = discord.Embed(title = self.displayname, description = f"Bedwars progress for {self.displayname} on {date.strftime('%m/%d/%y')}")

    d = self.to_embed_dict()
    for key in d.keys():
      value = d[key]
      embed.add_field(name = key, value = value, inline = False)

    return embed
    
class Bedwars(commands.Cog):

  def __init__(self, client):
    self.client = client
    

  @bridge.bridge_command(name="bw", aliases=["bedwars", "bwstats", "statsBW"], integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.self_argument
  async def bw(self, ctx, username: bridge.BridgeOption(str, description="The username of the player you want to see stats for.") = None, date: bridge.BridgeOption(str, description="Get stats for a specific date. Requires tracking.") = None):
    if username is None:
      await ctx.respond("Please provide a username or UUID.")
      return
    uuid = util.getUUID(username)
    
    if date is not None:
      if not CONFIG.TRACKING_ENABLED:
        await ctx.respond("Tracking is not enabled.")
        return

      date = parser.parse(date)

      stats_day = parse_from_json(databases.getJSON(date, uuid=uuid))
      stats_yesterday = parse_from_json(databases.getJSON(date - datetime.timedelta(days=1), uuid=uuid))
      stats = stats_day - stats_yesterday

      await ctx.respond(embed=stats.to_date_embed(date))
      return


    try:
      await ctx.respond(embed = BedwarsStats.get(CONFIG.KEY, uuid=uuid).to_embed())
    except Exception as e:
      await ctx.respond(f"Error while getting stats. Are you sure `{username}` is correct?")

  # TRACKING COMMANDS
  @bridge.bridge_command(name="today_bw", aliases=["todayBW"], integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.tracking_required
  @util.self_argument
  async def today_bw(self, ctx, username: bridge.BridgeOption(str, description="The username of the player who's stats you want to see.") = None):
    #checks
    if username is None:
      await ctx.respond("Please provide a valid username.")

    uuid = util.getUUID(username)

    if uuid is None:
      return

    if not tracking.track_contains(CONFIG.PATH, uuid):
      await ctx.respond(f"The player {username} is not being tracked.")
      return
    #checks


    wkdir = CONFIG.PATH + "/data/trackedplayers/" + uuid + "/"

    d_yesterday = datetime.datetime.now()

    today = BedwarsStats.get(key=CONFIG.KEY, uuid=uuid)
    yesterday = parse_from_json(databases.getJSON(d_yesterday, uuid=uuid))

    if yesterday is None:
      await ctx.respond(f"No tracking data for {username} yesterday.")

    data = today-yesterday

    embed = discord.Embed(title = data.displayname, description = f"{data.displayname}'s stats so far today.", color = 0x3498DB)
    embed = data.to_embed(embed=embed)

    await ctx.respond(embed = embed)

  @bridge.bridge_command(name="yesterday_bw", aliases=["yesterdayBW"], integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.tracking_required
  @util.self_argument
  async def yesterday_bw(self, ctx, username: bridge.BridgeOption(str, description="The username of the player who's stats you want to see.") = None): # type: ignore
    #checks
    if username is None:
      await ctx.respond("please provide a username or UsUID")

    uuid = util.getUUID(username)

    if uuid is None:
      return

    if not tracking.track_contains(CONFIG.PATH, uuid):
      await ctx.respond(f"The player {username} is not being tracked.")
      return
    #checks

    wkdir = CONFIG.PATH + "/dat/trackedplayers/" + uuid + "/"

    d_yesterday = datetime.datetime.now()
    d_daybefore = datetime.datetime.now() - datetime.timedelta(days=1)

    yesterday = parse_from_json(databases.getJSON(d_yesterday, uuid=uuid))
    daybefore = parse_from_json(databases.getJSON(d_daybefore, uuid=uuid))

    if yesterday is None or daybefore is None:
      await ctx.respond(f"Unable to get data. Ensure the player has been tracked for at least 2 days.")

    data = yesterday-daybefore

    date_formatted = d_yesterday.strftime("%m/%d/%y")

    embed = discord.Embed(title=data.displayname, description=f"{data.displayname}'s bedwars stats on {date_formatted}", color=0x206694)
    embed = data.to_embed(embed=embed)

    await ctx.respond(embed = embed)
