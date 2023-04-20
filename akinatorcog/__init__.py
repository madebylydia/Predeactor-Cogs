from .akinatorcog import Akinator


def setup(bot):
    cog: Akinator = Akinator(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog._killer(bot))
