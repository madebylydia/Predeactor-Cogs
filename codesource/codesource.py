import inspect
from typing import Literal

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu


class CodeSource(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.command(aliases=["sourcecode", "source", "code"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.is_owner()
    async def codesource(self, ctx: commands.Context, *, command: str):
        """
        Get the source code of a command.
        """
        command = self.bot.get_command(command)
        if command is None:
            await ctx.send("Command not found.")
            return
        try:
            source_code = inspect.getsource(command.callback)
        except OSError:
            await ctx.send("The command wasn't found, is it an InstantCmd command?")
            return
        temp_pages = [
            "```py\n" + str(page).replace("```", "`\u17b5``") + "```"
            for page in pagify(source_code, escape_mass_mentions=True, page_length=1980)
        ]

        max_i = len(temp_pages)
        pages = [f"Page {i}/{max_i}\n" + page for i, page in enumerate(temp_pages, start=1)]

        await menu(ctx, pages, controls=DEFAULT_CONTROLS)

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
