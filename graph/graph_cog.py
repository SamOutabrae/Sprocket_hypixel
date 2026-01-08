import discord
from discord.ext import commands

from ..config import CONFIG, both_in, guild_in
from .. import util
from . import graphing


# TODO implement commands for duels as well
class Graph(commands.Cog):
  def __init__(self):
    pass


  # TODO these options don't seem to actually be optional, fix that
  @commands.slash_command(name = "graph-bw")
  @util.self_argument
  @util.tracking_required
  async def graph_bw_command(self, ctx, 
                             username: discord.Option(str, description="The username of the player you're trying to see stats for"),
                             x_axis: discord.Option(str, description="The desired x-axis variable."),
                             y_axis: discord.Option(str, description="The desired y-axis variable")):
    # TODO make this code actually work
    """ if x_axis not in graphing.bw_variables or y_axis not in graphing.bw_variables:
      await ctx.respond(f"Both x_axis and y_axis must be valid and not None. Valid variables for graphing include [{", ".join(graphing.bw_variables.keys())}].")
      return """

    username = util.getUUID(username)

    if username is None:
      await ctx.respond("You must provide a valid username.")
      return 
    
    await graphing.graph_bw(ctx, username, x_axis, y_axis)
  