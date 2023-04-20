from redbot.core.bot import Red

from .captcher import Captcher

__red_end_user_data_statement__ = "This cog does not save data about users persistently."


def setup(bot: Red):
    cog = Captcher(bot)
    bot.add_cog(cog)
    the_grand_final = (
        "Hi, captain' speaking. I am the creator of Captcher. This cog is now outdated and "
        "officialy put in trash, meaning Captch**er** won't receive any new update.\n\nActually, "
        "you may be confused on this decision, but it happened because I decided to redo this "
        "cog from scratch, (From nothing) and so appear my new cog, **Captcha**, the "
        "BetterCaptcher of Captcher.\nThis cog will, of course, still work, but for the price "
        "of no support anymore, this ~beautiful~ message everytime you load this cog and you "
        "restart your bot, and no more update.\n\nI don't really know why you would do this, "
        "but feel free to. Captch**er** is made on very bad code, and is still in beta, this "
        "is just the worst idea to keep it.\n\nAnyway, if you decide to change to Captcha, I'm "
        "sad to announce you that I decided not to convert your data from Captcher, you will "
        "have to setup everything again... yep.\n\nThanks for the person who contribued to the "
        "creation of Captcher and that helped me find the bugs."
    )
    bot.loop.create_task(bot.send_to_owners(the_grand_final))
