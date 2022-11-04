import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from copyreg import constructor
import functools
from threading import Thread

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

class TrackParams(collections.namedtuple("TrackParams", "track condition season")):
    __slots__ = ()
    def __str__(self) -> str:
        return f"{self.track}-{'Wet' if self.condition else 'Dry'}-S{self.season}"

my_intents = Intents.default()
my_intents.message_content = True
bot = commands.Bot(command_prefix='$$', intents=my_intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

class LeaderboardCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.track = ""
        self.condition = 0
        self.season = 4
        self.simulate = False
        self.track_set: set[TrackParams] = set()
        super().__init__()
    
    async def set_params(self, track:str, condition:int, season:int):
        self.track = track
        self.condition = condition
        self.season = season
    
    async def get_params(self) -> constants.LeaderboardParams:
        return constants.LeaderboardParams(track_set=self.track_set, track=self.track, condition=self.condition, season=self.season)
    
    async def add_track(self, track_params:TrackParams) -> bool:
        if track_params.track not in constants.pretty_name_raw_name:
            return False
        self.track_set.add(track_params)
        return True
    
    async def remove_track(self, track_params:TrackParams) -> bool:
        if (not self.track_set) or (track_params not in self.track_set) or (track_params.track not in constants.pretty_name_raw_name):
            return False
        self.track_set.discard(track_params)
        return True
    
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
    
    async def cog_update_single(self, track_params:TrackParams):
        loop = asyncio.get_event_loop()
        backend = await loop.run_in_executor(
            ThreadPoolExecutor(),
            functools.partial(
                pj_leaderboard_backend.main,
                track=track_params.track,
                condition=track_params.condition,
                season=track_params.season,
                pages=None,
                simulate=self.simulate
            )
        )
        return backend

    @tasks.loop(hours=3)
    async def loop_update_leaderboard_multi(self):
        if not self.track_set:
            return constants.ErrorCode(1, "Track not set")
        else:
            for track in self.track_set:
                await self.cog_update_single(track_params=track)

    @tasks.loop(hours=3)
    async def loop_update_leaderboard(self):
        if not self.track:
            return constants.ErrorCode(1, "Track not set")
        else:
            await self.cog_update_leaderboard()

bot.add_cog(LeaderboardCog(bot))


@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="update_leaderboard_single", description="Update a single leaderboard")
async def updateldb_single(
    interaction: nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices=constants.discord_track_choices,
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
            "3" : 3,
            "4" : 4,
            "5" : 5
        }
    ),
    pages:int = nextcord.SlashOption(
        name="pages",
        required=False,
        default=0,
        description="Override the amount of pages to scrape. Enter 0 to disable."
    ),
    password:bool = nextcord.SlashOption(
        name="password",
        required=False,
        default=True,
        description="Closed lobby filter. Enabled by default. Disable only if you know what you're doing"
    ),
    simulate:bool = nextcord.SlashOption(
        name="simulation", 
        required=False,
        default=False,
        description="Simulation mode. Writes updated leaderboard to a file. Use this for testing"
    )
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
        embed.add_field(name="Pages override", value=pages, inline=True)
        embed.add_field(name="Password filter", value = password)
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
                    pages=pages if pages else None, 
                    pw=password,
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
        if (current_params.track_set):
            embed.add_field(name="Track set", value=','.join([t.__str__() for t in current_params.track_set]), inline=False)
    await interaction.followup.send(embed=embed)

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="set_leaderboard_parameters", description="Get the periodic update parameters")
async def set_current_ldb_params(
    interaction:nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices=constants.discord_track_choices,
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
            "3" : 3,
            "4" : 4,
            "5" : 5
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

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="add_track", description="Add track to periodic update group")
async def add_track_to_set(
    interaction:nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices=constants.discord_track_choices,
        description="Track to add"
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
            "3" : 3,
            "4" : 4,
            "5" : 5
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
            cd = ""
            track_params = TrackParams(track=track, condition=condition, season=season)
            track_params_str = f"{track_params.track}-{'Wet' if track_params.condition else 'Dry'}-S{track_params.season}"
            r = await leaderboard.add_track(track_params=track_params)
            if r:
                await interaction.followup.send(f"Added {track_params_str} to track set")
            else:
                await interaction.followup.send(f"Error adding {track_params_str} to track set")
        else:
            await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
            return

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="remove_track", description="Remove track from periodic update group")
async def remove_track_from_set(
    interaction:nextcord.Interaction,
    track:str = nextcord.SlashOption(
        name="track",
        choices=constants.discord_track_choices,
        description="Track to add"
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
            "3" : 3,
            "4" : 4,
            "5" : 5
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
            cd = ""
            track_params = TrackParams(track=track, condition=condition, season=season)
            track_params_str = f"{track_params.track}-{'Wet' if track_params.condition else 'Dry'}-S{track_params.season}"
            r = await leaderboard.remove_track(track_params=track_params)
            if r:
                await interaction.followup.send(f"Removed {track_params_str} from track set")
            else:
                await interaction.followup.send(f"Error removing {track_params_str} from track set")
        else:
            await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
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
        #leaderboard.loop_update_leaderboard.start()
        leaderboard.loop_update_leaderboard_multi.start()
        print("Loop started")
        next_it = leaderboard.loop_update_leaderboard_multi.next_iteration
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
        #leaderboard.loop_update_leaderboard.cancel()
        leaderboard.loop_update_leaderboard_multi.cancel()
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
        if current_params.track_set:
            embed.add_field(name="Track set", value=','.join([t.__str__() for t in current_params.track_set]), inline=False)
        next_it = leaderboard.loop_update_leaderboard_multi.next_iteration
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

@bot.slash_command(guild_ids=[constants.SRA_GUILD_ID], name="db_start", description="Start leaderboard update loop")
async def db_start(interaction:nextcord.Interaction):
    await interaction.response.defer()
    leaderboard:LeaderboardCog = bot.get_cog('LeaderboardCog')
    if leaderboard is not None:
        #leaderboard.loop_update_leaderboard.start()
        await leaderboard.loop_update_leaderboard_multi()
        print("Loop started")
        next_it = leaderboard.loop_update_leaderboard_multi.next_iteration
        if next_it:
            next_it_timestamp = next_it.timestamp()
            await interaction.followup.send(f"Loop started. Next iteration: <t:{int(next_it_timestamp)}:F>")
        else:
            await interaction.followup.send(f"Loop started")
    else:
        await interaction.followup.send("bot.get_cog('LeaderboardCog') returned None. Yell at Peter to troubleshoot")
    return
bot.run(keys.BOT_TOKEN)
