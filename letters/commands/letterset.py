from asyncio import TimeoutError as AsyncTimeoutError
from typing import Union

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from ..abc import MixinMeta


class LetterSet(MixinMeta):
    @commands.group(name="letterset")
    async def letter_set(self, ctx: commands.Context):
        """
        Set your options for letters you want to receive.
        """
        pass

    @letter_set.command(name="stop")
    async def stop_service(self, ctx: commands.Context):
        """
        Stop receiving/sending letter.
        """
        actual_state = await self.config.user(ctx.author).stop()
        if actual_state is False:
            react_to = await ctx.send(
                "**Every letter deserves to be delivered.** I, again, ask you to not "
                "stop using this service as, if someone wants to contact you, this is a good way "
                "for it, it would be hurtful for you to stop using it.\nIf you just want to "
                "'block' someone, use `[p]letterset blocklist` instead.\n\nAre you sure you want "
                "to stop using this service?".replace("[p]", ctx.clean_prefix)
            )
            start_adding_reactions(react_to, ReactionPredicate.YES_OR_NO_EMOJIS)
            predicate = ReactionPredicate.yes_or_no(react_to, ctx.author)
            try:
                await ctx.bot.wait_for("reaction_add", check=predicate, timeout=60)
            except AsyncTimeoutError:
                return
            if predicate.result:
                await self.config.user(ctx.author).stop.set(True)
                await ctx.send("Done.")
            else:
                await ctx.send("Good to know. 🙂")
            return
        await ctx.send("Activated the service Letter!")
        await self.config.user(ctx.author).stop.set(False)

    @letter_set.group(name="blocklist")
    async def blocklist(self, ctx: commands.Context):
        """
        Manage your letterbox's blocklist.
        """
        pass

    @blocklist.command(name="add")
    async def blocklist_add(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """
        Add someone in your blocklist.
        """
        if isinstance(user, discord.abc.User):
            user = user.id
        async with self.config.user(ctx.author).blocklist() as blocklist:
            if user in blocklist:
                await ctx.send("This user is already in your blocklist.")
                return
            blocklist.append(user)
        await ctx.send("I added the user in your blocklist.")

    @blocklist.command(name="remove", aliases=["del", "delete"])
    async def blocklist_remove(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """
        Remove someone from your blocklist.
        """
        if isinstance(user, discord.abc.User):
            user = user.id
        async with self.config.user(ctx.author).blocklist() as blocklist:
            if user not in blocklist:
                await ctx.send("This user is not in your blocklist.")
                return
            blocklist.remove(user)
        await ctx.send("I removed the user in your blocklist.")

    @blocklist.command(name="list")
    async def blocklist_list(self, ctx: commands.Context):
        """
        List IDs in the blocklist.
        """
        blocklist = await self.config.user(ctx.author).blocklist()
        if not blocklist:
            await ctx.send("It seems your blocklist is empty, that's good!")
            return
        msg = str("IDs in the blocklist:\n")
        async with ctx.typing():
            for u in blocklist:
                possible_user = await self.bot.get_or_fetch_user(int(u))
                msg += "\t- {id}: {user}".format(
                    id=str(u), user=possible_user.name if possible_user else "Not found."
                )
        for text in pagify(msg):
            await ctx.send(text)
