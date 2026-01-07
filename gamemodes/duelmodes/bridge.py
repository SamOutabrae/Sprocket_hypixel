import discord, requests, datetime
from ...util import get_prestige_halved, wins_to_prestige_halved
from ...tracking.databases import getJSON
from dataclasses import dataclass
from typing import Union
import logging

from ...config import CONFIG

@dataclass
class BridgeStats():
  username: str
  wins: int
  losses: int
  kills: int
  deaths: int
  gamesPlayed: int
  goals: int
  blocksPlaced: int
  highestWinstreak: Union[int, str]
  winstreak: Union[int, str]
  prestige: str
  nextPrestige: str
  winsToPrestige: int

  @classmethod
  def from_json(cls, json: dict):
    try:
      player_stats = json["player"]["stats"]["Duels"]
      username = json["player"]["displayname"]

      wins = (
        player_stats.get("bridge_duel_wins", 0) +
        player_stats.get("bridge_doubles_wins", 0) +
        player_stats.get("bridge_threes_wins", 0) +
        player_stats.get("bridge_four_wins", 0) +
        player_stats.get("bridge_3v3v3v3_wins", 0)
      )

      losses = (
        player_stats.get("bridge_duel_losses", 0) +
        player_stats.get("bridge_doubles_losses", 0) +
        player_stats.get("bridge_threes_losses", 0) +
        player_stats.get("bridge_four_losses", 0) +
        player_stats.get("bridge_3v3v3v3_losses")
      )

      kills = (
        player_stats.get("bridge_duel_bridge_kills", 0) +
        player_stats.get("bridge_doubles_bridge_kills", 0) +
        player_stats.get("bridge_threes_bridge_kills", 0) +
        player_stats.get("bridge_four_bridge_kills", 0) +
        player_stats.get("bridge_3v3v3v3", 0)
      )

      deaths = (
        player_stats.get("bridge_duel_bridge_deaths", 0) +
        player_stats.get("bridge_doubles_bridge_deaths", 0) +
        player_stats.get("bridge_threes_bridge_deahts", 0) +
        player_stats.get("bridge_four_bridge_deaths", 0) +
        player_stats.get("bridge_3v3v3v3_bridge_deaths", 0)
      )

      goals = (
        player_stats.get("bridge_duel_goals", 0) +
        player_stats.get("bridge_doubles_goals", 0) +
        player_stats.get("bridge_threes_goals", 0) +
        player_stats.get("bridge_four_goals", 0) +
        player_stats.get("bridge_3v3v3v3_goals", 0)
      )

      blocksPlaced = (
        player_stats.get("bridge_duel_blocks_placed", 0) +
        player_stats.get("bridge_doubles_blocks_placed", 0) +
        player_stats.get("bridge_threes_blocks_placed", 0) +
        player_stats.get("bridge_four_blocks_placed", 0) +
        player_stats.get("bridge_3v3v3v3_blocks_placed", 0)
      )

      gamesPlayed = wins + losses

      highestWinstreak = player_stats.get("best_bridge_winstreak", "This player has their winstreak hidden")
      winstreak = player_stats.get("current_bridge_winstreak", "This player has their winstreak hidden")

      prestige = get_prestige_halved(wins)
      next_prestige, wins_needed = wins_to_prestige_halved(wins)

      return cls(
        username=username,
        wins=wins,
        losses=losses,
        kills=kills,
        deaths=deaths,
        gamesPlayed=gamesPlayed,
        goals=goals,
        blocksPlaced=blocksPlaced,
        highestWinstreak=highestWinstreak,
        winstreak=winstreak,
        prestige=prestige,
        nextPrestige=next_prestige,
        winsToPrestige=wins_needed
      )

    except KeyError:
      return None

  def __add__(self, other):
      wins = self.wins + other.wins
      losses = self.losses + other.losses
      kills = self.kills + other.kills
      deaths = self.deaths + other.deaths
      goals = self.goals + other.goals
      blocksPlaced = self.blocksPlaced + other.blocksPlaced
      gamesPlayed = wins + losses

      prestige = get_prestige_halved(wins)
      next_prestige, wins_needed = wins_to_prestige_halved(wins)

      return BridgeStats(
          username=self.username,
          wins=wins,
          losses=losses,
          kills=kills,
          deaths=deaths,
          gamesPlayed=gamesPlayed,
          goals=goals,
          blocksPlaced=blocksPlaced,
          highestWinstreak=self.highestWinstreak,
          winstreak=self.winstreak,
          prestige=prestige,
          nextPrestige=next_prestige,
          winsToPrestige=wins_needed
      )
  
  def __sub__(self, other):
    wins = self.wins - other.wins
    losses = self.losses - other.losses
    kills = self.kills - other.kills
    deaths = self.deaths - other.deaths
    goals = self.goals - other.goals
    blocksPlaced = self.blocksPlaced - other.blocksPlaced
    gamesPlayed = wins + losses

    prestige = get_prestige_halved(self.wins)
    next_prestige, wins_needed = wins_to_prestige_halved(max(self.wins, other.wins))
  
    return BridgeStats(
        username=self.username,
        wins=wins,
        losses=losses,
        kills=kills,
        deaths=deaths,
        gamesPlayed=gamesPlayed,
        goals=goals,
        blocksPlaced=blocksPlaced,
        highestWinstreak=self.highestWinstreak,
        winstreak=self.winstreak,
        prestige=prestige,
        nextPrestige=next_prestige,
        winsToPrestige=wins_needed
    )
  
  def toEmbed(self, color=discord.Color.teal()):
    embed = discord.Embed(title=f"Bridge stats for {self.username}", color=color)

    fields = {
    "Prestige": self.prestige,
    "Next Prestige": f"{self.winsToPrestige} more wins for {self.nextPrestige}",
    "Highest Winstreak": self.highestWinstreak,
    "Current Winstreak": self.winstreak,
    "Games Played": self.gamesPlayed,
    "Win Rate": f"{round((self.wins*100)/(self.wins+self.losses))}%",
    "Wins": self.wins,
    "Losses": self.losses,
    "Kills": self.kills,
    "Deaths": self.deaths,
    "Goals": self.goals,
    "Blocks Placed": self.blocksPlaced
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)
    return embed
  
  def toDateEmbed(self, date, color=discord.Color.dark_teal()):
    date_formatted = date.strftime("%m/%d/%y")

    embed = discord.Embed(title=f"{self.username}'s bridge stats on {date_formatted}", color=color)

    fields = {
    "Prestige": self.prestige,
    "Highest Winstreak": self.highestWinstreak,
    "Current Winstreak": self.winstreak,
    "Games Played": self.gamesPlayed,
    "Win Rate": f"{round((self.wins*100)/(self.wins+self.losses))}%" if self.wins + self.losses != 0 else 0,
    "Wins": self.wins,
    "Losses": self.losses,
    "Kills": self.kills,
    "Deaths": self.deaths,
    "Goals": self.goals,
    "Blocks Placed": self.blocksPlaced
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)
  
    return embed

  def toDateRangeEmbed(self, start_date, end_date, color=discord.Color.dark_teal()):
    start_date_formatted = start_date.strftime("%m/%d/%y")
    end_date_formatted = end_date.strftime("%m/%d/%y")

    embed = discord.Embed(title=f"{self.username}'s bridge progress between {start_date_formatted} and {end_date_formatted}", color=color)

    fields = {
    "Games Played": self.gamesPlayed,
    "Win Rate": f"{round((self.wins*100)/(self.wins+self.losses))}%" if self.wins + self.losses != 0 else "N/A",
    "Wins": self.wins,
    "Losses": self.losses,
    "Kills": self.kills,
    "Deaths": self.deaths,
    "Goals": self.goals,
    "Blocks Placed": self.blocksPlaced
    }

    for field in fields:
      embed.add_field(name=field, value=fields[field], inline=False)
  
    return embed

def today_stats(uuid):
  json = requests.get(f"https://api.hypixel.net/player?key={CONFIG.KEY}&uuid={uuid}").json()
  return BridgeStats.from_json(json).toEmbed()

def getBridgeStatsEmbed(uuid, start_date, end_date):
  if start_date is None:
    return today_stats(uuid)
  elif end_date is None:
    #specific date
    if end_date == datetime.date.today():
      return today_stats(uuid)

    date = BridgeStats.from_json(getJSON(start_date, uuid=uuid))
    yesterday = BridgeStats.from_json(getJSON(start_date - datetime.timedelta(days=1), uuid=uuid))
    if date is None or yesterday is None:
      return None
    stats = date - yesterday

    return stats.toDateEmbed(start_date)
  else:
    #date_range
    start_json = getJSON(start_date, uuid=uuid)
    end_json = getJSON(end_date, uuid=uuid)

    if start_json is None or end_json is None:
      return None

    start_stats = BridgeStats.from_json(start_json)
    end_stats = BridgeStats.from_json(end_json)

    stats: BridgeStats = end_stats - start_stats

    return stats.toDateRangeEmbed(start_date, end_date)
