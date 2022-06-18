import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import functools

from discord import SlashOption
import constants
import pj_leaderboard_backend
import keys

import collections
from datetime import datetime, timezone
import math

import nextcord
from nextcord.ext.commands import context
from nextcord.ext import tasks
from nextcord.ext import commands
from nextcord import Intents


# Define a simple View that gives us a confirmation menu
class Confirm(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.value = False
        self.stop()

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


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

class LeaderboardCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.track = ""
        self.condition = 0
        self.season = 3
        self.simulate = False
        super().__init__()
    
    async def set_params(self, track:str, condition:int, season:int):
        self.track = track
        self.condition = condition
        self.season = season
    
    async def get_params(self) -> constants.LeaderboardParams:
        return constants.LeaderboardParams(track=self.track, condition=self.condition, season=self.season)
    
    async def cog_update_leaderboard(self):
        loop = asyncio.get_event_loop()
        backend = await loop.run_in_executor(
            ThreadPoolExecutor(),
            functools.partial(
                pj_leaderboard_backend.main,
                track=self.track,
                condition=self.condition,
                season=self.season,
                pages=None,
                simulate=self.simulate
            )
        )
        return backend
        #pj_leaderboard_backend.main(track=self.track, condition=self.condition, season=self.season, pages=None, simulate=simulate)
    
    @tasks.loop(hours=3)
    async def loop_update_leaderboard(self):
        if not self.track:
            return constants.ErrorCode(1, "Track not set")
        else:
            await self.cog_update_leaderboard()

bot.add_cog(LeaderboardCog(bot))

@bot.command()
async def setup(ctx, params:str):
    if (params not in constants.setup_dict.keys()):
        await ctx.channel.send("Git gud kid")
    else:
        await ctx.channel.send(constants.setup_dict[params])
    return



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


@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="update_leaderboard_single", description="Update a single leaderboard")
async def updateldb_single(
    interaction: nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices={
            "Barcelona" : "barcelona",
            "Brands Hatch" : "brands_hatch",
            "Donington" : "donington",
            "Hungaroring" : "hungaroring",
            "Imola" : "imola",
            "Kyalami" : "kyalami",
            "Laguna Seca" : "laguna_seca",
            "Misano" : "misano",
            "Monza" : "monza",
            "Mount Panorama" : "mount_panorama",
            "Nurburgring" : "nurburgring",
            "Oulton Park" : "oulton_park",
            "Paul Ricard" : "paul_ricard",
            "Silverstone" : "silverstone",
            "Snetterton" : "snetterton",
            "Spa" : "spa",
            "Suzuka" : "suzuka",
            "Zolder" : "zolder",
            "Zandvoort" : "zandvoort"
        },
        description="Track to update"
    ),
    condition:int = nextcord.SlashOption(
        name="condition",
        choices={
            "Dry" : 0,
            "Wet" : 1
        },
        description="Track condition"
    ),
    season:int = nextcord.SlashOption(
        name="season",
        choices={
            "1" : 1,
            "2" : 2,
            "3" : 3
        }
    ),
    simulate:bool = nextcord.SlashOption(name="simulation", description="Simulation mode. Writes updated leaderboard to a file. Use this for testing")
):
    if not (interaction.user.get_role(constants.SRA_ADMIN_ROLE_ID) or interaction.user.get_role(constants.SRA_TECH_ROLE_ID)):
        await interaction.response.send_message("You're not authorized to use this command")
    else:
        await interaction.response.defer()
        embed = nextcord.Embed()
        embed.title = "Leaderboard update parameters"
        embed.add_field(name="Simulation mode", value=simulate, inline=False)
        embed.add_field(name="Track", value=track, inline=True)
        embed.add_field(name="Condition", value="Wet" if condition else "Dry", inline=True)
        embed.add_field(name="Season", value=season, inline=True)
        view = Confirm()
        await interaction.followup.send(embed=embed, view=view)
        await view.wait()
        if view.value is None:
            print("Timed out...")
        elif view.value:
            print("Confirmed...")
            loop = asyncio.get_event_loop()
            backend = loop.run_in_executor(
                ThreadPoolExecutor(), 
                functools.partial(
                    pj_leaderboard_backend.main, 
                    track=track, 
                    condition=condition, 
                    season=season, 
                    pages=None, 
                    simulate=simulate
                )
            )
            await interaction.channel.send(f"Updated ")
            return backend
        else:
            print("Cancelled...")
    
    
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="get_leaderboard_parameters", description="Get the periodic update parameters")
async def get_current_ldb_params(interaction:nextcord.Interaction):
    await interaction.response.defer()
    embed = nextcord.Embed()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        current_params = await leaderboard.get_params()
        print(current_params)
        embed = nextcord.Embed()
        embed.title = "Leaderboard parameters"
        embed.add_field(name="Current track", value=current_params.track if current_params.track else "None", inline=True)
        embed.add_field(name="Current condition", value="Wet" if current_params.condition else "Dry", inline=True)
        embed.add_field(name="Current season", value=current_params.season, inline=True)
    await interaction.followup.send(embed=embed)

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="set_leaderboard_parameters", description="Get the periodic update parameters")
async def get_current_ldb_params(
    interaction:nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices={
            "Barcelona" : "barcelona",
            "Brands Hatch" : "brands_hatch",
            "Donington" : "donington",
            "Hungaroring" : "hungaroring",
            "Imola" : "imola",
            "Kyalami" : "kyalami",
            "Laguna Seca" : "laguna_seca",
            "Misano" : "misano",
            "Monza" : "monza",
            "Mount Panorama" : "mount_panorama",
            "Nurburgring" : "nurburgring",
            "Oulton Park" : "oulton_park",
            "Paul Ricard" : "paul_ricard",
            "Silverstone" : "silverstone",
            "Snetterton" : "snetterton",
            "Spa" : "spa",
            "Suzuka" : "suzuka",
            "Zolder" : "zolder",
            "Zandvoort" : "zandvoort"
        },
        description="Track to update"
    ),
    condition:int = nextcord.SlashOption(
        name="condition",
        choices={
            "Dry" : 0,
            "Wet" : 1
        },
        description="Track condition"
    ),
    season:int = nextcord.SlashOption(
        name="season",
        choices={
            "1" : 1,
            "2" : 2,
            "3" : 3
        }
    )
):
    if not (interaction.user.get_role(constants.SRA_ADMIN_ROLE_ID) or interaction.user.get_role(constants.SRA_TECH_ROLE_ID)):
        await interaction.response.send_message("You're not authorized to use this command")
    else:
        await interaction.response.defer()
        leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
        if leaderboard is not None:
            current_params = await leaderboard.get_params()
            print(current_params)
            embed = nextcord.Embed()
            embed.title = "Leaderboard update parameters"
            embed.add_field(name="Current track", value=current_params.track if current_params.track else "None", inline=True)
            embed.add_field(name="Current condition", value="Wet" if current_params.condition else "Dry", inline=True)
            embed.add_field(name="Current season", value=current_params.season, inline=True)
            embed.add_field(name="New track", value=track, inline=True)
            embed.add_field(name="New condition", value="Wet" if condition else "Dry", inline=True)
            embed.add_field(name="New season", value=season, inline=True)
        else:
            await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
            return

        view = Confirm()
        await interaction.followup.send(embed=embed, view=view)
        await view.wait()
        if view.value is None:
            print("Timed out...")
        elif view.value:
            print("Confirmed...")
            if leaderboard is not None:
                await leaderboard.set_params(track=track, condition=condition, season=season)
                print(await leaderboard.get_params())
        else:
            print("Cancelled...")
    
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="get_simulate_mode", description="Get simulation mode status")
async def get_simulate(interaction:nextcord.Interaction):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        await interaction.followup.send(leaderboard.simulate)
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="set_simulate_mode", description="Set simulation mode status")
async def set_simulate(
    interaction:nextcord.Interaction,
    simulate:bool = nextcord.SlashOption(name="simulation", description="Simulation mode. Writes updated leaderboard to a file. Use this for testing")
):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        leaderboard.simulate = simulate
        await interaction.followup.send(f"New simulate status:{leaderboard.simulate}")
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="start_update_loop", description="Start leaderboard update loop")
async def start_update_loop(interaction:nextcord.Interaction):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        leaderboard.loop_update_leaderboard.start()
        print("Loop started")
        next_it = leaderboard.loop_update_leaderboard.next_iteration
        if next_it:
            next_it_timestamp = next_it.timestamp()
            await interaction.followup.send(f"Loop started. Next iteration: <t:{int(next_it_timestamp)}:F>")
        else:
            await interaction.followup.send(f"Loop started")
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="stop_update_loop", description="Stop leaderboard update loop")
async def stop_update_loop(interaction:nextcord.Interaction):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        leaderboard.loop_update_leaderboard.cancel()
        await interaction.followup.send(f"Loop stopped")
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="loop_status", description="Get loop status")
async def get_loop_status(interaction:nextcord.Interaction):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        current_params = await leaderboard.get_params()
        print(current_params)
        embed = nextcord.Embed()
        embed.title = "Leaderboard parameters"
        embed.add_field(name="Current track", value=current_params.track if current_params.track else "None", inline=True)
        embed.add_field(name="Current condition", value="Wet" if current_params.condition else "Dry", inline=True)
        embed.add_field(name="Current season", value=current_params.season, inline=True)
        embed.add_field(name="Simulation mode", value=leaderboard.simulate, inline=True)
        embed.add_field(name="Current iteration", value=leaderboard.loop_update_leaderboard.current_loop, inline=True)
        next_it = leaderboard.loop_update_leaderboard.next_iteration
        next_it_timestamp = 0.0
        if next_it:
            next_it_timestamp = next_it.timestamp()
        embed.add_field(name="Next iteration", value=f"<t:{int(next_it_timestamp)}:F>" if next_it else "N/A", inline=True)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return

@tasks.loop(seconds=30)
async def say_hi(greeting):
    await bot.get_channel(constants.CONTROL_CHANNEL_ID).send(greeting)

@bot.command()
async def start_loop(ctx):
    await ctx.channel.send("Started loop")
    await say_hi.start("Howdy!")

@bot.command()
async def stop_loop(ctx):
    await ctx.channel.send("Stopped loop")
    say_hi.cancel()

@bot.command()
async def restart_loop(ctx):
    await ctx.channel.send("Restarted loop")
    say_hi.restart("Howdy!")

@bot.command()
async def check_loop(ctx):
    if say_hi.is_running():
        await ctx.channel.send("Loop running")
    else:
        await ctx.channel.send("Loop not running")

bot.run(keys.BOT_TOKEN)
