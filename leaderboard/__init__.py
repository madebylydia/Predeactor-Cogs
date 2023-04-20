from .leaderboard import LeaderBoard

__red_end_user_data_statement__ = (
    "This cog store data about users persistently for saving data. Red may store "
    "your discord ID with your settings you set and how many points you got."
)


def setup(bot):
    bot.add_cog(LeaderBoard(bot))
