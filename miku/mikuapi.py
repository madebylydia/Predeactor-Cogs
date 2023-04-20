from typing import Literal
from urllib.parse import urljoin

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

BASE_URL = "https://miku-for.us"


class Miku(commands.Cog):
    """
    The first Miku images API.
    """

    __author__ = ["Predeactor"]
    __version__ = "v1.1"

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {humanize_list(self.__author__)}\nCog Version: {self.__version__}"

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

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def miku(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get(urljoin(BASE_URL, "/api/v2/random")) as response:
                if response.status == 503:
                    await ctx.send("The API is actually in maintenance, please retry later.")
                    return
                try:
                    status = response.status
                    url = await response.json()
                except aiohttp.ContentTypeError:
                    await ctx.send(
                        (
                            "API unavailable. Status code: {code}\nIt may be due of a "
                            + "maintenance."
                        ).format(code=status)
                    )
                    return
        embed = discord.Embed(
            title="Here's a pic of Hatsune Miku!", color=await self.bot.get_embed_colour(ctx)
        )
        try:
            embed.set_image(url=url["url"])
        except KeyError:
            await ctx.send(f"I received an incorrect format from the API\nStatus code: {status}")
            return
        embed.set_footer(text="From https://miku-for.us")
        await ctx.send(embed=embed)
