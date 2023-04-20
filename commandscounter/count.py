from traceback import format_exception
from typing import Literal

import discord
from discord.ext.commands.errors import (
    CommandNotFound,
    ConversionError,
    MissingRequiredArgument,
    NSFWChannelRequired,
)
from redbot.core import commands
from redbot.core.commands.errors import ConversionFailure
from redbot.core.utils.chat_formatting import (
    box,
    humanize_list,
    inline,
    pagify,
)
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

IGNORE_ERRORS_TYPE = (
    CommandNotFound,
    MissingRequiredArgument,
    NSFWChannelRequired,
    ConversionFailure,
    commands.UserFeedbackCheckFailure,
    ConversionError,
)


class CommandsCounter(commands.Cog):
    """Count all commands used."""

    __author__ = ["Predeactor"]
    __version__ = "v2.0.2"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        """
        Nothing to delete...
        """
        pass

    def __init__(self, bot):
        self.bot = bot
        self.commands = {}
        super(CommandsCounter, self).__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    @commands.group(invoke_without_command=True)
    async def count(self, ctx: commands.Context, *, command: str):
        """Know how many time a command has been used.

        If the command had an error one time, it will also be shown.
        """
        str_command = command.lower()
        if str_command in self.commands:
            message = "{command} has been used {count} time since last reboot".format(
                command=inline(str_command), count=self.commands[str_command]["count"]
            )
            if self.commands[str_command]["error"] >= 1:
                message += ", and sent an error {error} time".format(
                    error=self.commands[str_command]["error"]
                )
            message += "."
            await ctx.send(message)
        else:
            await ctx.send(
                "{command} hasn't been used, yet...".format(command=inline(str_command))
            )

    @count.command()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def all(self, ctx: commands.Context):
        """List all commands and how many time they have been used."""
        message = "\n".join(
            "- {cmd}: Used {count} time.".format(cmd=inline(d[0]), count=d[1]["count"])
            for d in sorted(
                self.commands.items(),
                key=lambda infos: infos[1]["count"],
                reverse=True,
            )
        )

        embeds = []
        embed_base = discord.Embed(
            color=await ctx.embed_color(), title="All commands usage since last reboot:"
        )
        embed_base.set_footer(
            text="Requested by {author}".format(author=ctx.author.name),
            icon_url=ctx.author.avatar_url,
        )
        for text in pagify(message):
            again_embed = embed_base.copy()
            again_embed.description = text
            embeds.append(again_embed)

        if len(embeds) > 1:
            await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=300)
        elif embeds:
            await ctx.send(embed=embeds[0])
        else:
            await ctx.send("No commands has been used so far.")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.message.author.bot is False:
            command = str(ctx.command)
            if command != "None":
                if command not in self.commands:
                    self.commands[command] = {"count": 1, "error": 0}
                    return
                self.commands[command]["count"] += 1

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        try:
            if isinstance(error, IGNORE_ERRORS_TYPE):
                return

            if not ctx.message.author.bot:
                command = str(ctx.command)
                if command not in self.commands:
                    self.commands[command] = {"count": 0, "error": 1}
                    return
                self.commands[command]["error"] += 1
        except Exception:
            pass
