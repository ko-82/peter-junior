import constants
import pj_leaderboard
import keys

from typing import NamedTuple, Type
import collections
import re
from datetime import date, datetime, timedelta, timezone
import math
import argparse
import urllib.parse
from os import path
import platform

import nextcord
from nextcord.ext.commands import context
from nextcord.ext.commands.flags import convert_flag
from nextcord.ext import tasks
from nextcord.ext import commands
from nextcord import Intents

from pyppeteer import launch

my_intents = Intents.default()
my_intents.message_content = True
bot = commands.Bot(command_prefix='$$', intents=my_intents)

def calc_fuel(total_time:int, lap_time_str:str, fuel_per_lap:float):
    lap_time = datetime.strptime(lap_time_str, '%M:%S.%f')
    lap_time_mins = lap_time.minute + lap_time.second/60 + lap_time.microsecond/60000000
    laps = math.ceil(total_time/lap_time_mins) + 1
    laps_fm = laps + 1
    total_fuel = math.ceil(laps * fuel_per_lap)
    total_fuel_fm = math.ceil(laps_fm * fuel_per_lap)
    (f"Total {total_time} minutes\n{lap_time_mins}m per lap\n{fuel_per_lap}L per lap\nFuel needed: {total_fuel}L\nFuel needed with full formation lap: {total_fuel_fm}L")
    Fuel = collections.namedtuple("Fuel", ["min", "fm"])
    
    return Fuel(total_fuel, total_fuel_fm)

def get_leaderboard(track:str) -> pj_leaderboard.Leaderboard:
    filename = path.join("csvs", f"{track}.csv")
    leaderboard = pj_leaderboard.Leaderboard.read_leaderboard(file_path=filename)
    leaderboard.track = track
    return leaderboard

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def ssshelp(ctx):
    await ctx.channel.send("Good day. Peter Junior at your service")
    await ctx.channel.send(
        (
            f"Available commands:"
            f"$$setup help"
            f"$$fuel"
        )
    )
    return

@bot.command()
async def setup(ctx, params:str):
    if (params not in constants.setup_dict.keys()):
        await ctx.channel.send("Git gud kid")
    else:
        await ctx.channel.send(constants.setup_dict[params])
    return

@bot.command()
async def fuel(ctx, params:str):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("total_time", type=int, nargs='?')
    parser.add_argument("lap_time", type=str, nargs='?')
    parser.add_argument("fuel_per_lap", type=float, nargs='?')
    parser.add_argument("--help", action='store_true')
    args = parser.parse_args(params.split())
    print(args)

    if (args.help):
        await ctx.channel.send(
            (
                f"Calculate fuel based on race time and lap time\n"
                f'Syntax: $$fuel "<total_time_in_mins> <lap_time> <fuel_per_lap>"\n'
                f"Lap time must be in mm:ss.SSS format\n"
                f'Example: $$fuel "60 02:21.500 3.8"\n'
            )
        )
        return
    if not (args.total_time and args.lap_time and args.fuel_per_lap):
        print("Invalid syntax")
        return
    
    fuel = calc_fuel(args.total_time, args.lap_time, args.fuel_per_lap)
    await ctx.channel.send(
        (
            f"Total {args.total_time} minutes\n"
            f"{args.lap_time} per lap\n"
            f"{args.fuel_per_lap}L per lap\n"
            f"Fuel needed: {fuel.min}L\n"
            f"Fuel needed with full formation lap: {fuel.fm}L\n"
        )
    )
    return

@bot.command(name="updateldb")
async def update_leaderboard(ctx, track, pages = 3, pw = True):
    leaderboard = get_leaderboard(track=track)
    leaderboard.update(pages=pages, pw=pw)
    await ctx.channel.send("Updated")
    leaderboard.write_leaderboard(path.join("csvs", f"{leaderboard.track}.csv"))


@bot.command(name="db_timestamp")
async def db_timestamp(ctx):
    now = datetime.now(timezone.utc)
    timestamp = now.timestamp()
    await ctx.channel.send(f"<t:{int(timestamp)}:F>")

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="fuel")
async def fuel_slash(
    interaction: nextcord.Interaction,
    total_time: int = nextcord.SlashOption(name="total_time", description="Total race time"),
    lap_time: str = nextcord.SlashOption(name="lap_time", description="Average lap time in mm:ss.SSS format"),
    fuel_per_lap: float = nextcord.SlashOption(name="fuel_per_lap", description="Fuel consumed per lap")
):
    total_fuel = calc_fuel(total_time, lap_time, fuel_per_lap)
    await interaction.response.send_message(
        (
            f"Total {total_time} minutes\n"
            f"{lap_time} per lap\n"
            f"{fuel_per_lap}L per lap\n"
            f"Fuel needed: {total_fuel.min}L\n"
            f"Fuel needed with full formation lap: {total_fuel.fm}L\n"
        )
    )

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="update_leaderboard")
async def updateldb_slash(
    interaction: nextcord.Interaction,
    track: str = nextcord.SlashOption(name="track", description="Track to update"),
    pages: int = nextcord.SlashOption(name="pages", description="Number of pages to scrape"),
    pw: bool = nextcord.SlashOption(name="pw", description="Limit to password protected sessions. Set to true unless you're Peter and you're messing around")
):
    if not (interaction.user.get_role(constants.SRA_ADMIN_ROLE_ID) or interaction.user.get_role(constants.SRA_TECH_ROLE_ID)):
        await interaction.response.send_message("You're not authorized to use this command")
    else:
        await interaction.response.defer()
        #TODO: Figure out how to call bot.updateldb() from here
        leaderboard = get_leaderboard(track=track)
        leaderboard.update(pages=pages, pw=pw)
        leaderboard.write_leaderboard(path.join("csvs", f"{leaderboard.track}.csv"))
        await interaction.followup.send(f"Updated {pages} of {track} with password {pw}")

class LeaderboardCog(commands.Cog):
    def __init__(self) -> None:
        self.bot = bot
        super().__init__()
    
    @tasks.loop(hours=2)
    async def update_leaderboard():
        pass

@tasks.loop(seconds=30)
async def say_hi(greeting):
    await bot.get_channel(constants.CONTROL_CHANNEL_ID).send(greeting)

@bot.command()
async def start_loop(ctx):
    await ctx.channel.send("Started loop")
    await say_hi.start("Howdy!")

@bot.command()
async def restart_loop(ctx):
    await ctx.channel.send("Restarted loop")
    say_hi.restart("Howdy!")

@bot.command()
async def ping(ctx):
    await ctx.reply('Pong!')

bot.run(keys.BOT_TOKEN)
