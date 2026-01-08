import discord
from discord.ext.commands import Context

from ..tracking import databases

import pandas as pd
import matplotlib.pyplot as plt
from dateutil import parser

import os

# Turn interactive mode off so we don't show plots
plt.ioff()

bw_variables = {
  "Date": ["Date"],
  "Kills": ["Kills"],
  "Deaths": ["Deaths"], 
  "Void Deaths": ["Void Deaths"], 
  "Final Deaths":  ["Final Deaths"], 
  "Final Kills": ["Final Kills"], 
  "Beds Broken": ["Beds Broken"], 
  "Bedwars Level": ["Bedwars Level", "Level"],
  "Games Played": ["Games Played", "Games"],
  "Wins": ["Wins"],
  "Losses": ["Losses"],
  "K/D Ratio": ["K/D Ratio", "KDR"],
  "Final K/D Ratio": ["Final K/D Ratio", "FKDR"]
}

# TODO make this function nicer
def match_bedwars_variable(var: str) -> str:
  var = var.lower()

  for key, aliases in bw_variables.items():
    if var in [a.lower() for a in aliases]:
      return key

# TODO create a nicer user interface
async def graph_bw(ctx: Context, uuid: str, x_label: str, y_label):
  df: pd.DataFrame = databases.databases[uuid]

  df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%y")
  df = df.sort_values("Date")

  y_label = match_bedwars_variable(y_label)
  x_label = match_bedwars_variable(x_label)

  fig, ax = plt.subplots()
  ax.plot(df[x_label], df[y_label])

  fig.autofmt_xdate()

  ax.set_title(f"Bedwars Stats")
  ax.set_ylabel(f"{y_label}")
  ax.set_xlabel(f"{x_label}")

  fig.savefig("tmp.jpeg")
  await ctx.respond(file=discord.File("tmp.jpeg"))
  os.remove("tmp.jpeg")
  
  plt.close(fig)

  
