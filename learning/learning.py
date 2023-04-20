import asyncio
from typing import Literal

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import humanize_list

from .lessons import Lessons


class Learning(commands.Cog):

    """This cog is made for learning the Python basics and how to make your own cog on Red.

    Cog has reached EoL (End of Life), it mean that I won't give support, enhancement,
     new lessons or anything else to this cog. However, you can open a pull request
     and do change by yourself."""

    __author__ = ["Predeactor"]
    __version__ = "Last - EoL"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        await self.data.user_from_id(user_id).clear()

    def __init__(self, bot):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=495954054)

        self.data.register_user(lvl1=False, lvl2=False, lvl3=False)
        self.lessons = Lessons()
        super().__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    @commands.group(name="learningpython")
    @checks.bot_has_permissions(embed_links=True)
    async def lpy(self, ctx: commands.GuildContext):
        """Here, you will learn the Python's basics."""
        pass

    @lpy.command(name="introduction")
    async def intro(self, ctx: commands.Context):
        """Introduction first of all all."""
        intro_list = self.lessons.pintro()
        for data in intro_list:
            if isinstance(data, int):
                await asyncio.sleep(data)
            else:
                embed = discord.Embed(
                    title="Introduction",
                    color=await self.bot.get_embed_colour(ctx),
                    description=data,
                )
                await ctx.send(embed=embed)
        await self.data.user(ctx.author).lvl1.set(True)

    @lpy.command(name="references")
    async def ref(self, ctx: commands.Context):
        """Some useful links to learn more on Python."""
        refs_list = self.lessons.pref()
        for data in refs_list:
            if isinstance(data, int):
                await asyncio.sleep(data)
            else:
                embed = discord.Embed(
                    title="References",
                    color=await self.bot.get_embed_colour(ctx),
                    description=data,
                )
                await ctx.send(embed=embed)

    @lpy.command(name="level1")
    async def lv1(self, ctx: commands.Context):
        """Start level 1.

        Let's learn how to install Python and run it."""
        if await self.data.user(ctx.author).lvl1() is False:
            await ctx.send("Please read the introduction first of all.")
            return
        datas_list = self.lessons.plvl1()
        for data in datas_list:
            if isinstance(data, int):
                await asyncio.sleep(data)
            else:
                embed = discord.Embed(
                    title="Installing and launching Python",
                    color=await self.bot.get_embed_colour(ctx),
                    description=data,
                )
                await ctx.send(embed=embed)
        await self.data.user(ctx.author).lvl2.set(True)

    @lpy.command(name="level2")
    async def lv2(self, ctx: commands.Context):
        """Start the level 2.

        Let's learn how to use variables."""
        if await self.data.user(ctx.author).lvl2() is False:
            await ctx.send(
                "Uh oh, seem you didn't even completed the level 1. I won't let you learn variables if you don't know "
                "how to launch Python. "
            )
            return
        datas_list = self.lessons.plvl2()
        for data in datas_list:
            if isinstance(data, int):
                await asyncio.sleep(data)
            else:
                embed = discord.Embed(
                    title="Variables",
                    color=await self.bot.get_embed_colour(ctx),
                    description=data,
                )
                await ctx.send(embed=embed)
        await self.data.user(ctx.author).lvl3.set(True)

    @lpy.command(name="level3")
    async def lv3(self, ctx: commands.Context):
        """Start the level 3.

        Let's learn the differents datas type."""
        if await self.data.user(ctx.author).lvl3() is False:
            await ctx.send("Uh oh, seem you didn't even completed the level 2.")
            return
        datas_list = self.lessons.plvl3()
        for data in datas_list:
            if isinstance(data, int):
                await asyncio.sleep(data)
            else:
                embed = discord.Embed(
                    title="Type of Datas",
                    color=await self.bot.get_embed_colour(ctx),
                    description=data,
                )
                await ctx.send(embed=embed)
