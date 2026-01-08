import discord
from discord.ext.commands import Context

from ..tracking import databases

import pandas as pd
import matplotlib.pyplot as plt

import os

# Turn interactive mode off so we don't show plots
plt.ioff()

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
    embed.add_field(name=key, value=f"{", ".join(bw_variables[key])}", inline=False)

  return embed

async def graph_bw(ctx: Context, uuid: str, x_label: str, y_label):
  df: pd.DataFrame = databases.databases[uuid]

  df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%y")
  df = df.sort_values("Date")

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