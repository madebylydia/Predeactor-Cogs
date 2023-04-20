import math
import operator
from datetime import datetime
from typing import Literal

import discord
from redbot.core import Config, commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import (
    box,
    humanize_list,
    humanize_timedelta,
)


class LeaderBoard(commands.Cog):
    """
    Leaderboard, using a point system.
    For everyone who use the bot constantly.
    """

    __author__ = ["Predeactor"]
    __version__ = "v1.0.3"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        if requester == ("discord_deleted_user" or "user_strict"):
            await self.data.user_from_id(user_id).clear()

    def __init__(self, bot):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=82466655781)
        self.data.register_user(points=0, mention=True, next_reputation=0)
        self.data.register_global(cooldown_time=21600)
        super(LeaderBoard, self).__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    @commands.command()
    @commands.guild_only()
    async def rep(self, ctx: commands.Context, *, user: discord.User):
        """Give a reputation point to another user!"""
        current_time = round(datetime.timestamp(datetime.now()))
        reputation_point_cool = await self.data.user(ctx.author).next_reputation()
        cooldown_time = await self.data.cooldown_time()
        next_cooldown = reputation_point_cool + cooldown_time
        if user.bot:
            await ctx.send(
                "We are the robots. Robot can't receive reputation points"
                " because they already are too popular!"
            )
            return
        if user == ctx.author:
            await ctx.send(
                "Uhm, I don't think I can allow you to give you reputation"
                " points to yourself... :)"
            )
            return
        if current_time <= next_cooldown:
            await ctx.send(
                "Oh no! You have to wait `{time}`.".format(
                    time=humanize_timedelta(seconds=next_cooldown - current_time)
                )
            )
            return
        await self._give_rep(ctx, user, current_time)

    @commands.group()
    async def repset(self, ctx: commands.GuildContext):
        """Settings for reputation."""
        pass

    @repset.command()
    async def mention(self, ctx: commands.Context, mention: bool):
        """Choose if I mention you when someone give you a reputation point.

        For mention, option are True or False.
        """
        await self.data.user(ctx.author).mention.set(mention)
        await ctx.send("Mention setting set to `{bool}`".format(bool=mention))

    @repset.command()
    @commands.is_owner()
    async def cooldown(self, ctx: commands.Context, time_in_seconds: int):
        """Set the cooldown time between each reputation points given.

        Default to `21600`. (6 hours)
        Time must be given in seconds.
        """
        if time_in_seconds < 60:
            await ctx.send("Time must be longer than 1 minute.")
            return
        if time_in_seconds > 2 ** 64:
            await ctx.send(
                "I won't allow you to go over this point. (Btw, can you tell me why you want to"
                "give only ONE points in your misearable life?)"
            )
        await self.data.cooldown_time.set(time_in_seconds)
        await ctx.send(
            "Done. Peoples will be able to give another point of reputation after {time} "
            "({seconds}).".format(
                time=humanize_timedelta(seconds=time_in_seconds), seconds=time_in_seconds
            )
        )

    async def _give_rep(
        self, ctx: commands.Context, user: discord.User, current_time_as_seconds: int
    ):
        user_points = await self.data.user(user).points()
        await self.data.user(user).points.set(user_points + 1)

        await ctx.send(
            "**{receiver} received a reputation point from {author}!\nYou now"
            " have {reps} reputation point{plural}.**".format(
                receiver=await self._user_mention(user),
                author=ctx.author,
                reps=user_points + 1,
                plural="s" if user_points > 0 else "",
            )
        )

        await self.data.user(ctx.author).next_reputation.set(current_time_as_seconds)

    async def _user_mention(self, user):
        if await self.data.user(user).mention():
            return user.mention
        return user

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def repboard(self, ctx, page_list: int = 1):
        """Show the reputation leaderboard.
        Give a number to show a page.
        """
        users = []
        title = "Global Rep Leaderboard for {}\n".format(self.bot.user.name)
        all_users = await self.data.all_users()
        if str(all_users) == "{}":
            await ctx.send("The leaderboard is empty... Nobody's popular, for now.")
            return
        for user_id in all_users:
            user_name = await self._get_user_name(user_id)
            users.append((user_name, all_users[user_id]["points"]))
            if ctx.author.id == user_id:
                user_stat = all_users[user_id]["points"]

        board_type = "Rep"
        icon_url = self.bot.user.avatar_url
        sorted_list = sorted(users, key=operator.itemgetter(1), reverse=True)
        rank = 1
        for allusers in sorted_list:
            if ctx.author.name == allusers[0]:
                author_rank = rank
                break
            rank += 1
        footer_text = "Your Rank: {}                      {}: {}".format(
            author_rank, board_type, user_stat
        )

        # multiple page support
        page = 1
        per_page = 15
        pages = math.ceil(len(sorted_list) / per_page)
        if 1 <= page_list <= pages:
            page = page_list
        else:
            await ctx.send("**Please enter a valid page number! (1 - {})**".format(str(pages)))
            return

        msg = ""
        msg += "Rank     Name                   (Page {}/{})     \n\n".format(page, pages)
        rank = 1 + per_page * (page - 1)
        start_index = per_page * page - per_page
        end_index = per_page * page

        default_label = "  "
        special_labels = ["♔", "♕", "♖", "♗", "♘", "♙"]

        async for single_user in AsyncIter(sorted_list[start_index:end_index]):
            if rank - 1 < len(special_labels):
                label = special_labels[rank - 1]
            else:
                label = default_label

            msg += "{:<2}{:<2}{:<2} # {:<15}".format(
                rank, label, "➤", await self._truncate_text(single_user[0], 15)
            )
            msg += "{:>5}{:<2}{:<2}{:<5}\n".format(
                " ", " ", " ", " {}: ".format(board_type) + str(single_user[1])
            )
            rank += 1
        msg += "--------------------------------------------            \n"
        msg += "{}".format(footer_text)

        em = discord.Embed(description="", colour=await self.bot.get_embed_colour(ctx))
        em.set_author(name=title, icon_url=icon_url)
        em.description = box(msg)

        await ctx.send(embed=em)

    @staticmethod
    async def _truncate_text(text, max_length):
        if len(text) > max_length:
            return text[: max_length - 1] + "…"
        return text

    async def _get_user_name(self, user_id: int):
        user = self.bot.get_user(user_id)
        if user is None:  # User not found
            try:
                user = await self.bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                return "Unknown User"
        return user.name
