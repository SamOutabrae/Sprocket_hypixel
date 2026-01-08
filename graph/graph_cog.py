import discord
from discord.ext import commands

from ..config import CONFIG, both_in, guild_in
from .. import util
from . import graphing


# TODO implement commands for duels as well
class Graph(commands.Cog):
  def __init__(self):
    pass


  @commands.slash_command(name = "graph-bw", integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.self_argument
  @util.tracking_required
  async def graph_bw_command(self, ctx, 
                             y_axis: discord.Option(str, description="The desired y-axis variable."),
                             x_axis: discord.Option(str, default="Games", description="The desired x-axis variable. Defaults to games if left blank"),
                             username: discord.Option(str, required=False, description="The username of the player you're trying to see stats for.")):
    await ctx.defer()
    username = util.getUUID(username)

    if username is None:
      await ctx.respond("You must provide a valid username.")
      return 
    
    await graphing.graph_bw(ctx, username, x_axis, y_axis)
  
  @commands.slash_command(name = "graph-duels", integration_types = both_in if CONFIG.ALLOW_USER_INSTALLS else guild_in)
  @util.self_argument
  @util.tracking_required
  async def graph_duels(self, ctx,
                        duelmode: discord.Option(str, description="The duels gamemode you want to graph."),
                        y_axis: discord.Option(str, description="The desired y-axis variable."),
                        x_axis: discord.Option(str, default="Games", description="The desired x-axis variable. Defaults to games if left blank."),
                        username: discord.Option(str, required=False, description="The username of the player you're trying to see stats for")):
    #await ctx.defer()

    # TODO add UHC
    gamemodes = {
      'bridge': graphing.graph_bridge,
    }

    # TODO add nicer user interface
    if not duelmode.lower() in gamemodes:
      await ctx.respond("You must provide a valid gamemode.")
      return
    func = gamemodes[duelmode.lower()]

    uuid = util.getUUID(username)
    if uuid is None:
      await ctx.respond("You must provide a valid username.")
      return
    
    await func(ctx, duelmode, uuid, x_axis, y_axis)