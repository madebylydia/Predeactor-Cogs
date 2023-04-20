from .learning import Learning

__red_end_user_data_statement__ = "This cog will save your ID if you use the cog as intended."


def setup(bot):
    bot.add_cog(Learning(bot))
