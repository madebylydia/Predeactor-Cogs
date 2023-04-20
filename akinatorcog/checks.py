from redbot.core.commands import Context, check

DEVS_IDS = (
    669223041322057769,
    131813999326134272,
)


def testing_check():
    async def predicate(ctx: Context):
        """We don't like spam, at Red, section #testing."""
        if (
            ctx.channel.id in (133251234164375552,)
            and ctx.author.id not in DEVS_IDS
            and not await ctx.bot.is_owner(ctx.author)
        ):
            if ctx.invoked_with != "help":
                await ctx.send("No no no! I won't let you get smashed by Defender! - Pred.")
            return False
        return True

    return check(predicate)


need_child_mode: bool = lambda x: not x.nsfw
