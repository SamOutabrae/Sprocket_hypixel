from discord.ext import commands, bridge
import discord
from .. import util
import logging
from ..config import CONFIG, both_in, guild_in
from typing import Optional

from dateutil import parser
from datetime import datetime


from .duelmodes.bridge import get_bridge_stats_embed
from .duelmodes.uhc import get_UHC_stats_embed

duelmodes = {
  "bridge": get_bridge_stats_embed,
  "uhc": get_UHC_stats_embed
}

class Duels(commands.Cog):
  def __init__(self):
    pass

  async def _duels_stats(self, ctx, duelmode, start, end, username):
    uuid = util.getUUID(username)

    if uuid is None:
      await ctx.respond(f"Please ensure {username} is a proper username.")
      return
    
    if duelmode is None:
      await ctx.respond("You must provide a duelmode.")
      return

    if CONFIG.TRACKING_ENABLED:
      if start is not None:
        today_synonyms = ["today", "t"]
        start = datetime.today() if start in today_synonyms else parser.parse(start)
      
      if end is not None:
        end = parser.parse(end)
    else:
      if start is not None or end is not None:
        await ctx.respond("Tracking is not enabled. Ignoring date arguments.")

      start = None
      end = None

    duelmode = duelmode.lower()
    if duelmode not in duelmodes:
      await ctx.respond(f"No duelmode {duelmode}. Please ensure you enter a proper duelmode.")

    embed = None
    try:
      embed = duelmodes[duelmode](uuid, start, end)
      if embed is None:
        await ctx.respond(f"Data out of range. Please ensure you request a date range for which data exists.")
        return
    except Exception as e:
      logging.error(e)
      await ctx.respond(f"Error while getting stats.")
      return

    await ctx.respond(embed=embed)

  @bridge.bridge_command(name="today_duels", integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.self_argument
  async def today_duels(self,
                        ctx, 
                        duelmode: bridge.BridgeOption(str, choices=["bridge", "uhc"])=None, 
                        username: bridge.BridgeOption(str, description="The username of the person you want to see stats for.")=None):
    await self._duels_stats(ctx, duelmode, "t", None, username)

  @bridge.bridge_command(name="duels", integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.self_argument
  async def duels(self, ctx, duelmode: bridge.BridgeOption(str, choices=["bridge", "uhc"]), 
                  start: bridge.BridgeOption(str, description="The start date for a range. If you just want stats for today you can also just put t.")=None, 
                  end: bridge.BridgeOption(str, description="The end date for a range. Can be left blank.")=None, 
                  username: bridge.BridgeOption(str, description="The username of the person you want to see stats for.")=None):
    await self._duels_stats(ctx, duelmode, start, end, username)