import discord
import itertools
import os
import traceback

from typing import Tuple
from glob import glob

from discord.flags import MemberCacheFlags
from discord import Intents, AllowedMentions
from discord.ext import commands, tasks
from discord.ext.commands import AutoShardedBot

from config.ext.config_parser import config

from utils.console import console
from utils.logging import log

class GrovestreetBot(AutoShardedBot):
    def __init__(self, *args, **kwargs):

        # Tuple of all activities the bot will display as a status
        self.activities = itertools.cycle(
            (
                discord.Activity(
                    type=discord.ActivityType.watching, name="Packing Community #1"
                ),
                lambda: discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"Babysantana & Kashdami + Slump6",
                ),
            )
        )

        # Declaring intents and initalizing parent class
        intents = Intents.all()
        stuff_to_cache = MemberCacheFlags.from_intents(intents)
        mentions = AllowedMentions(everyone=False, roles=False)
        super().__init__(
            intents=intents,
            command_prefix=self.determine_prefix,
            case_insensitive=True,
            help_command=None,
            allowed_mentions=mentions,
            member_cache_flags=stuff_to_cache,
            chunk_guilds_at_startup=False,
            max_messages=1000,
            *args,
            **kwargs,
        )

        self.load_extensions()

    async def determine_prefix(self, bot: commands.Bot, message: discord.Message) -> str:
        guild = message.guild
        if guild:
            return commands.when_mentioned_or('-')(bot, message)

    def load_extensions(
        self, reraise_exceptions: bool = False
    ) -> Tuple[Tuple[str], Tuple[str]]:
        loaded_extensions = set()
        failed_extensions = set()
        for file in map(
            lambda file_path: file_path.replace(os.path.sep, ".")[:-3],
            glob("cogs/**/*.py", recursive=True),
        ):
            try:
                self.load_extension(file)
                loaded_extensions.add(file)
                log.info(
                    f"[bright_green][EXTENSION][/bright_green] [cyan1]{file} LOADED[/cyan1]"
                )
            except Exception as e:
                failed_extensions.add(file)
                log.info(
                    f"[bright red][EXTENSION ERROR][/bright red] [cyan1]FAILED TO LOAD COG {file}[/cyan1]"
                )
                if not reraise_exceptions:
                    traceback.print_exception(type(e), e, e.__traceback__)
                else:
                    raise e
        result = (tuple(loaded_extensions), tuple(failed_extensions))
        return result

    def _start(self) -> None:
        self.run(config["DISCORD_TOKEN"], reconnect=True)

    @tasks.loop(seconds=10)
    async def status(self):
        """Cycles through all status every 10 seconds"""
        new_activity = next(self.activities)
        # The commands one is callable so the command counts actually change
        if callable(new_activity):
            await self.change_presence(
                status=discord.Status.online, activity=new_activity()
            )
        else:
            await self.change_presence(
                status=discord.Status.online, activity=new_activity
            )

    @status.before_loop
    async def before_status(self) -> None:
        """Ensures the bot is fully ready before starting the task"""
        await self.wait_until_ready()

    async def on_ready(self) -> None:
        """Called when we have successfully connected to a gateway"""

        console.print(
            "[cyan1]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan1]"
        )
        console.print(
            """[cyan1]

 ██████╗ ██████╗  ██████╗ ██╗   ██╗███████╗███████╗████████╗██████╗ ███████╗███████╗████████╗    
██╔════╝ ██╔══██╗██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝  
██║  ███╗██████╔╝██║   ██║██║   ██║█████╗  ███████╗   ██║   ██████╔╝█████╗  █████╗     ██║         
██║   ██║██╔══██╗██║   ██║╚██╗ ██╔╝██╔══╝  ╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══╝     ██║        
╚██████╔╝██║  ██║╚██████╔╝ ╚████╔╝ ███████╗███████║   ██║   ██║  ██║███████╗███████╗   ██║       
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝  
                                                                                                                           
[/cyan1]"""
        )

        console.print(
            f"[cyan1]Signed into Discord as {self.user} (ID: {self.user.id}[/cyan1])\n"
        )
        console.print(f"[cyan1]Discord Version: {discord.__version__}[/cyan1]")
        console.print(
            "[cyan1]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan1]"
        )
        self.status.start()


# Defining root level commands
bot = GrovestreetBot()

if __name__ == "__main__":
    # Makes sure the bot only runs if this is run as main file
    try:
        bot._start()
    except Exception as e:
        log.exception(e)
