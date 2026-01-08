import discord
from discord.ext.commands import Context

from ..tracking import databases

import pandas as pd
import matplotlib.pyplot as plt

import datetime

import os

# Turn interactive mode off so we don't show plots
plt.ioff()

def process_df(df: pd.DataFrame, days: int=0, n: int=0, since_start: bool=True) -> pd.DataFrame:
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%y", dayfirst=True)
    df = df.sort_values("Date")

    if n > 0:
        df = df.tail(n)
    if days > 0:
        latest = df['Date'].max()
        df = df[df['Date'] >= (latest - datetime.timedelta(days=days))]

    if df.empty:
        return df

    if since_start:
        # Identify columns that should NOT be zeroed
        # Level is cumulative, but people usually want to see absolute level (e.g., 150 -> 151)
        # Winstreaks are current states, not cumulative totals.
        ignore_cols = ["Date", "Bedwars Level", "Winstreak", "Highest Winstreak"]
        
        cols_to_zero = df.select_dtypes(include=['number']).columns
        cols_to_zero = [c for c in cols_to_zero if c not in ignore_cols and "Ratio" not in c and "Rate" not in c]

        df[cols_to_zero] = df[cols_to_zero].subtract(df[cols_to_zero].iloc[0])

    return df
# TODO as a n parameter so you can see only recent data

bw_variables = {
  "Date": ["date", "time"],
  "Kills": ["kills"],
  "Deaths": ["deaths"], 
  "Void Deaths": ["void deaths"], 
  "Final Deaths":  ["final deaths"], 
  "Final Kills": ["final kills"], 
  "Beds Broken": ["beds broken"], 
  "Bedwars Level": ["bedwars level", "level"],
  "Games Played": ["games played", "games"],
  "Wins": ["wins"],
  "Losses": ["losses"],
  "K/D Ratio": ["k/d ratio", "kdr"],
  "Final K/D Ratio": ["final k/d ratio", "fkdr"],
  "Win Rate": ["win rate", "winrate", "wr"]
}

def match_bedwars_variable(var: str) -> str:
  var = var.lower()

  for key in bw_variables:
    if var in bw_variables[key]:
      return key

def get_bw_axis(df, label):
  if label == "Win Rate":
    return df["Wins"] / (df["Wins"] + df["Losses"])
  else:
    return df[label]

# TODO this is better than before but still kind of ugly
def bad_bw_labels_embed() -> discord.Embed:
  embed = discord.Embed(title="Invalid Axis Names", description="Valid axis names include the following. Aliases are provided below.", color=discord.colour.Color.blue())
  for key in bw_variables:
    embed.add_field(name=key, value=f"{', '.join(bw_variables[key])}", inline=False)

  return embed

async def graph_bw(ctx: Context, uuid: str, x_label: str, y_label: str, days: int, n: int):
  df: pd.DataFrame = databases.databases[uuid]["bedwars"]
  df = process_df(df, days, n)  
  
  y_label = match_bedwars_variable(y_label)
  x_label = match_bedwars_variable(x_label)

  if x_label is None or y_label is None:
    await ctx.respond(embed=bad_bw_labels_embed())
    return
  
  x_axis = get_bw_axis(df, x_label)
  y_axis = get_bw_axis(df, y_label)

  fig, ax = plt.subplots()
  ax.plot(x_axis, y_axis)

  fig.autofmt_xdate()

  ax.set_title(f"Bedwars Stats")
  ax.set_ylabel(f"{y_label}")
  ax.set_xlabel(f"{x_label}")

  fig.savefig("tmp.jpeg")
  await ctx.respond(file=discord.File("tmp.jpeg"))
  os.remove("tmp.jpeg")
  
  plt.close(fig)




bridge_variables = {
  "Date": ["date", "time"],
  "Kills": ["kills"],
  "Deaths": ["deaths"], 
  "Games Played": ["games played", "games"],
  "Goals": ["goals"],
  "Blocks Placed": ["blocks placed", "blocks"],
  "Wins": ["wins"],
  "Losses": ["losses"],
  "Highest Winstreak": ["highest winstreak", "hws"],
  "Win Rate": ["win rate", "winrate", "wr"]
}

def match_bridge_variable(var: str) -> str:
  var = var.lower()

  for key in bridge_variables:
    if var in bridge_variables[key]:
      return key

def get_bridge_axis(df, label):
  if label == "Win Rate":
    return df["Wins"] / (df["Wins"] + df["Losses"])
  else:
    return df[label]
  
def bad_bridge_labels_embed() -> discord.Embed:
  embed = discord.Embed(title="Invalid Axis Names", description="Valid axis names include the following. Aliases are provided below.", color=discord.colour.Color.blue())
  for key in bridge_variables:
    embed.add_field(name=key, value=f"{', '.join(bridge_variables[key])}", inline=False)

  return embed

async def graph_bridge(ctx: Context, duelmode: str, uuid: str, x_label: str, y_label: str, days: int, n: int):
  df: pd.DataFrame = databases.databases[uuid]["bridge"]
  df = process_df(df, days, n)

  y_label = match_bridge_variable(y_label)
  x_label = match_bridge_variable(x_label)

  if x_label is None or y_label is None:
    await ctx.respond(embed=bad_bridge_labels_embed())
    return
  
  x_axis = get_bridge_axis(df, x_label)
  y_axis = get_bridge_axis(df, y_label)

  fig, ax = plt.subplots()
  ax.plot(x_axis, y_axis)

  fig.autofmt_xdate()

  ax.set_title(f"Bridge Stats")
  ax.set_ylabel(f"{y_label}")
  ax.set_xlabel(f"{x_label}")

  fig.savefig("tmp.jpeg")
  await ctx.respond(file=discord.File("tmp.jpeg"))
  os.remove("tmp.jpeg")
  
  plt.close(fig)