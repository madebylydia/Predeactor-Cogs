from .count import CommandsCounter

__red_end_user_data_statement__ = "This cog does not save data about users persistently."


def setup(bot):
    bot.add_cog(CommandsCounter(bot))
