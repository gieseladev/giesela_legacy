import logging

from discord import ClientException, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Command, Context, HelpCommand

from giesela import MAIN_VERSION, SUB_VERSION
from giesela.lib import GieselaHelpCommand

log = logging.getLogger(__name__)


class InfoCog(commands.Cog, name="Info"):
    _prev_help_command: HelpCommand

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._prev_help_command = bot.help_command
        bot.help_command = GieselaHelpCommand()

    @property
    def help_command(self) -> HelpCommand:
        return self.bot.help_command

    def cog_unload(self) -> None:
        self.bot.help_command = self._prev_help_command

    @commands.Cog.listener()
    async def on_ready(self):
        for command in self.bot.commands:
            self.ensure_help_sub_command(command)

    def ensure_help_sub_command(self, group: commands.Group):
        if not isinstance(group, commands.Group):
            return

        async def func(ctx: Context, *parts: str) -> None:
            command = " ".join((group.name, *parts))
            await self.help_command.command_callback(ctx, command=command)

        func.__module__ = __package__
        sub_cmd = Command(func, name="help", aliases=["?"], hidden=True, help=f"Help for {group.qualified_name}")

        try:
            group.add_command(sub_cmd)
        except ClientException:
            log.debug(f"{group} already has a help function")

    @commands.command()
    async def version(self, ctx: Context):
        """Some more information about the current version and what's to come."""
        desc = f"Giesela v`{MAIN_VERSION}` (**{SUB_VERSION}**)"

        em = Embed(title=f"Version", description=desc, colour=0x67BE2E)

        await ctx.send(embed=em)


def setup(bot: Bot):
    bot.add_cog(InfoCog(bot))
