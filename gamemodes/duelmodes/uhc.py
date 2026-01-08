import discord, requests, datetime

from ...util import get_prestige, wins_to_prestige

from dataclasses import dataclass

from ...tracking.databases import getJSON

from ...config import CONFIG
from typing import Optional 

@dataclass
class UHCStats():
  username: str
  prestige: str
  next_prestige: tuple[str, int]
  wins: int
  losses: int
  kills: int
  deaths: int
  games_played: int
  golden_apples_eaten: int
  damage_dealt: int
  blocks_placed: int
  highest_winstreak: Optional[int]
  winstreak: Optional[int]
  bow_hits: int
  bow_shots: int

  @classmethod
  def from_json(cls, json_data: dict):
    if not json_data.get("success", False):
      return None

    try:
      stats    = json_data["player"]["stats"]["Duels"]
      username = json_data["player"]["displayname"]
      wins     = stats.get("uhc_duel_wins", 0)

      return cls(
        username          = username,
        wins              = wins,
        prestige          = get_prestige(wins),
        next_prestige     = wins_to_prestige(wins),
        losses            = stats.get("uhc_duel_losses", 0),
        kills             = stats.get("uhc_duel_kills", 0),
        deaths            = stats.get("uhc_duel_deaths", 0),
        gamesPlayed       = stats.get("uhc_duel_rounds_played", 0),
        goldenApplesEaten = stats.get("uhc_duel_golden_apples_eaten", 0),
        damageDealt       = stats.get("uhc_duel_damage_dealt", 0),
        blocksPlaced      = stats.get("uhc_duel_blocks_placed", 0),
        highest_winstreak = stats.get("best_uhc_winstreak", "This player has their winstreak hidden."),
        winstreak         = stats.get("current_uhc_winstreak", "Thjis player has their winstreak hidden."),
        bow_hits          = stats.get("uhc_duel_bow_hits", 0),
        bow_shots         = stats.get("uhc_duel_bow_shots", 0)
      )

    except KeyError:
      return None

  def __sub__(self, other):
    wins                = self.wins - other.wins
    losses              = self.losses - other.losses
    kills               = self.kills - other.kills
    deaths              = self.deaths - other.deaths
    games_played        = self.games_played - other.games_played
    golden_apples_eaten = self.golden_apples_eaten - other.golden_apples_eaten
    damage_dealt        = self.damage_dealt - other.damage_dealt
    blocks_placed       = self.blocks_placed - other.blocks_placed
    bow_hits            = self.bow_hits - other.bow_hits
    bow_shots           = self.bow_shots - other.bow_shots

    return UHCStats(
      username            = self.username,
      winstreak           = self.winstreak,
      highest_winstreak   = self.highest_winstreak,
      wins                = wins,
      prestige            = get_prestige(self.wins),
      next_prestige       = wins_to_prestige(self.wins),
      losses              = losses,
      kills               = kills,
      deaths              = deaths,
      games_played        = games_played,
      golden_apples_eaten = golden_apples_eaten,
      damage_dealt        = damage_dealt,
      blocks_placed       = blocks_placed,
      bow_hits            = bow_hits,
      bow_shots           = bow_shots
    )

  def to_embed(self, color=discord.Color.teal()):
    embed = discord.Embed(title=f"UHC stats for {self.username}", color=color)

    next_prestige, wins_needed = self.next_prestige

    fields = {
      "Prestige"           : self.prestige,
      "Next Prestige"      : f"{wins_needed} more wins for {next_prestige}",
      "Highest Winstreak"  : self.highest_winstreak,
      "Current Winstreak"  : self.winstreak,
      "Games Played"       : self.games_played,
      "Wins"               : self.wins,
      "Losses"             : self.losses,
      "Win Percentage"     : f"{round(self.wins * 100 / (self.wins + self.losses))}%" if self.wins + self.losses != 0 else 0,
      "Kills"              : self.kills,
      "Deaths"             : self.deaths,
      "Bow Accuracy"       : f"{round((self.bow_hits / (self.bow_shots + self.bow_hits)) * 100, 2)}%" if self.bow_shots + self.bow_hits != 0 else 0,
      "Golden Apples Eaten": self.golden_apples_eaten,
      "Damage Dealt"       : self.damage_dealt,
      "Blocks Placed"      : self.blocks_placed
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)

    return embed   
  
  def to_date_embed(self, date, color=discord.Color.teal()):
    embed = discord.Embed(title=f"{self.username}'s uhc duels stats on {date.strftime('%m/%d/%y')}", color=color)

    next_prestige, wins_needed = self.next_prestige

    fields = {
      "Prestige"           : self.prestige,
      "Next Prestige"      : f"{wins_needed} more wins for {next_prestige}",
      "Highest Winstreak"  : self.highest_winstreak,
      "Games Played"       : self.games_played,
      "Wins"               : self.wins,
      "Losses"             : self.losses,
      "Win Percentage"     : f"{round(self.wins * 100 / (self.wins + self.losses))}%" if self.wins + self.losses != 0 else 0,
      "Kills"              : self.kills,
      "Deaths"             : self.deaths,
      "Bow Accuracy"       : f"{round((self.bow_hits / (self.bow_shots + self.bow_hits)) * 100, 1)}%" if self.wins + self.losses != 0 else 0,
      "Golden Apples Eaten": self.golden_apples_eaten,
      "Damage Dealt"       : self.damage_dealt,
      "Blocks Placed"      : self.blocks_placed
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)

    return embed   
  
    
  def to_date_range_embed(self, start_date, end_date, color=discord.Color.teal()):
    start_date_formatted = start_date.strftime("%m/%d/%y")
    end_date_formatted = end_date.strftime("%m/%d/%y")

    embed = discord.Embed(title=f"{self.username}'s uhc duels progress between {start_date_formatted} and {end_date_formatted}", color=color)

    fields = {
      "Games Played"       : self.games_played,
      "Win Rate"           : f"{round((self.wins*100)/(self.wins+self.losses))}%" if self.wins + self.losses != 0 else "N/A",
      "Wins"               : self.wins,
      "Losses"             : self.losses,
      "Kills"              : self.kills,
      "Deaths"             : self.deaths,
      "Golden Apples Eaten": self.golden_apples_eaten,
      "Damage Dealt"       : self.damage_dealt,
      "Blocks Placed"      : self.blocks_placed
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)

    return embed   
    
def today_stats(uuid):
  json = requests.get(f"https://api.hypixel.net/player?key={CONFIG.KEY}&uuid={uuid}").json()
  return UHCStats.from_json(json).to_embed()

def get_UHC_stats_embed(uuid: str, start_date: datetime.datetime | None, end_date: datetime.datetime | None):
  if start_date is None:
    today_stats(uuid)
  
  #specific date
  elif end_date is None:
    if start_date == datetime.date.today():
      return today_stats(uuid)
    
    date = UHCStats.from_json(getJSON(start_date, uuid=uuid))
    yesterday = UHCStats.from_json(getJSON(start_date - datetime.timedelta(days=1), uuid=uuid))
    stats = date - yesterday
  
    return stats.to_date_embed(start_date)
  
  #date range
  else:
    start_json = getJSON(start_date, uuid=uuid)
    end_json = getJSON(end_date, uuid=uuid)

    start_stats = UHCStats.from_json(start_json)
    end_stats = UHCStats.from_json(end_json)

    stats: UHCStats = end_stats - start_stats

    return stats.to_date_range_embed(start_date, end_date)