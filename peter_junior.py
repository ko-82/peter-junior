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
from nextcord import user
from nextcord.ext import commands

from pyppeteer import launch


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

def get_leaderboard(track:str) -> pj_leaderboard.Leaderboard:
    filename = path.join("csvs", f"{track}.csv")
    leaderboard = pj_leaderboard.Leaderboard.read_leaderboard(file_path=filename)
    leaderboard.track = track
    return leaderboard

async def pyp_html_screenshot(html_path, html_dir_path):
    html_path_abs = path.abspath(html_path).replace("\\","/")
    html_url = urllib.parse.quote(html_path_abs, safe=":/")
    img_path = path.join(html_dir_path, "table.png")

    if ("arm" in platform.machine()):
        print("ARM")
        browser = await launch({"executablePath": "/usr/bin/chromium-browser"})     #Pyppeteer uses x86 Chromium on ARM for some unholy reason
    else:
        browser = await launch()
    print("Browser launched...")
    page = await browser.newPage()
    await page.setViewport({"width": 1280, "height": 720})
    response = await page.goto(f"file:///{html_url}")
    element = await page.querySelector(".ldb-table")
    await element.screenshot(path=img_path)
    print("Scr taken...")
    await browser.close()
    print("Browser closed...")

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

@bot.command(name="printldb")
async def print_leaderboard(ctx, track):
    leaderboard = get_leaderboard(track=track)
    leaderboard.write_leaderboard(file_path=path.join("print", f"{leaderboard.track}.txt"), suppress_id=True, space_delim=True, trail_trim=True)
    await ctx.channel.send(file=nextcord.File(fp=path.join("print", f"{leaderboard.track}.txt")))
    
@bot.command(name="printldbshort")
async def print_leaderboard_short(ctx, track):
    leaderboard = get_leaderboard(track=track)
    ldb_embed = leaderboard.generate_embed_compatible()
    embed = nextcord.Embed(title=f"{leaderboard.track} leaderboard")
    embed.add_field(name="Driver", value=ldb_embed.driver, inline=True)
    embed.add_field(name="Car", value=ldb_embed.car, inline=True)
    embed.add_field(name="Time", value=ldb_embed.time, inline=True)
    embed.timestamp = leaderboard.last_updated

    await ctx.channel.send(embed=embed)


@bot.command(name="genscr")
@commands.has_role('Admin')
async def generate_screenshot(ctx, track):
    leaderboard = get_leaderboard(track=track)
    leaderboard.to_html()
    print("HTML done")
    await pyp_html_screenshot(leaderboard.get_html_path(), leaderboard.get_html_dir_path())
    print("Screenshot taken")

    if not path.exists(path.join(leaderboard.get_html_dir_path(), "table.png")):
        await ctx.channel.send("No image file")
    else:
        with open(path.join(leaderboard.get_html_dir_path(), "table.png"), "rb") as f:
            image = nextcord.File(f)
            await ctx.channel.send(f"Last updated: <t:{int(leaderboard.last_updated.timestamp())}:F>",file=image)
    print("Done")

@bot.command(name="db_timestamp")
async def db_timestamp(ctx):
    now = datetime.now(timezone.utc)
    timestamp = now.timestamp()
    await ctx.channel.send(f"<t:{int(timestamp)}:F>")

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID])
async def choose_a_number(
    interaction: nextcord.Interaction,
    number: str = nextcord.SlashOption(name="settings", description="Configure Your Settings")
):
    await interaction.response.send_message(f"You chose {number}")

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
        

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="print_leaderboard")
async def print_leaderboard_slash(
    interaction: nextcord.Interaction,
    track: str = nextcord.SlashOption(name="track", description="Track to print the leaderboard for"),
):
    leaderboard = get_leaderboard(track=track)
    leaderboard.write_leaderboard(file_path=path.join("print", f"{leaderboard.track}.txt"), suppress_id=True, space_delim=True, trail_trim=True)
    await interaction.response.send_message(file=nextcord.File(fp=path.join("print", f"{leaderboard.track}.txt")))

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="generate_screenshot")
async def generate_screenshot_slash(
    interaction: nextcord.Interaction,
    track: str = nextcord.SlashOption(name="track", description="Track to print the leaderboard for"),
):
    if not (interaction.user.get_role(constants.SRA_ADMIN_ROLE_ID) or interaction.user.get_role(constants.SRA_TECH_ROLE_ID)):
        await interaction.response.send_message("You're not authorized to use this command")
    else:
        await interaction.response.defer()
        leaderboard = get_leaderboard(track=track)
        leaderboard.to_html()
        print("HTML done")
        await pyp_html_screenshot(leaderboard.get_html_path(), leaderboard.get_html_dir_path())
        print("Screenshot taken")

        if not path.exists(path.join(leaderboard.get_html_dir_path(), "table.png")):
            await interaction.followup.send("No image file")
        else:
            with open(path.join(leaderboard.get_html_dir_path(), "table.png"), "rb") as f:
                image = nextcord.File(f)
                await interaction.followup.send(f"Last updated: <t:{int(leaderboard.last_updated.timestamp())}:F>",file=image)
        print("Done")


bot.run(keys.BOT_TOKEN)