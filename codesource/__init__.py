from .codesource import CodeSource


def setup(bot):
    cog = CodeSource(bot)
    bot.add_cog(cog)
