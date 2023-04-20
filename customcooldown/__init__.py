from .customcooldown import CustomCooldown

__red_end_user_data_statement__ = (
    "This cog store data about users persistently for required reasons. Red may store "
    "where and when you send your last message, depending cog's parameter (If sent in a"
    " channel/category in cooldown) as your Discord's ID."
)


async def setup(bot):
    cog = CustomCooldown(bot)
    bot.add_cog(cog)
    # noinspection PyProtectedMember
    await cog._maybe_update_config()
