from .mikuapi import Miku


def setup(bot):
    bot.add_cog(Miku(bot))
