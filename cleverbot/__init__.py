from .cleverbot import CleverBot

__red_end_user_data_statement__ = "This cog does not save data about users persistently."


async def setup(bot):
    bot.add_cog(CleverBot(bot))
