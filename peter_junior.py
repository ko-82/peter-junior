import constants
import keys
from typing import NamedTuple, Type
import collections
import re
from datetime import datetime, timedelta
import math
import argparse

import nextcord
from nextcord.ext.commands import context
from nextcord.ext.commands.flags import convert_flag
from nextcord import user
from nextcord.ext import commands
from nextcord.ext import tasks


bot = commands.Bot(command_prefix='$$')

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
        await ctx.channel.send("Command not found")
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
bot.run(keys.BOT_TOKEN)