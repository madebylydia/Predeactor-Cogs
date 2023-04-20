from discord import Embed
from random import choice
from typing import Literal, Mapping, Optional

from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

from .asynccleverbot import cleverbot as ac

seems_ok = None


class Core(commands.Cog):

    __author__ = ["Predeactor"]
    __version__ = "v1.2"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        """
        Nothing to delete...
        """
        pass

    # Nothing to delete, I assume that if the user was previously in self.conversation,
    # then it will automatically removed after cog reload/bot restart.

    def __init__(self, bot: Red):
        self.bot = bot
        self.conversation = {}
        super().__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    @commands.Cog.listener()
    async def on_red_api_tokens_update(self, service_name: str, api_tokens: Mapping):
        global seems_ok
        if service_name == "travitia":
            seems_ok = None

    async def _get_api_key(self):
        travitia = await self.bot.get_shared_api_tokens("travitia")
        # No need to check if the API key is not registered, the
        # @apicheck() do it automatically.
        return travitia.get("api_key")

    async def _make_cleverbot_session(self):
        return ac.Cleverbot(await self._get_api_key())

    @staticmethod
    async def ask_question(session, question: str, user_id: int):
        try:
            answer = await session.ask(user_id, question)
            answered = True
        except Exception as e:
            answer = "An error happened: {error}\nPlease try again later. Session closed.".format(
                error=str(e)
            )
            answered = False
        return answer, answered

    # Commands for settings

    @commands.is_owner()
    @commands.has_permissions(embed_links=True)
    @commands.command()
    async def travitiaapikey(self, ctx: commands.Context):
        """Gives instructions for obtaining the API key for Travitia API.

        Thanks to Rhodz for agreeing using Purpose's lyrics
        Nice easter egg, uhm? :)
        """
        purpose = [
            "Have you ever seen the sky falling\nOpen up your tired eyes, keep watching\nYou don't always have to shine the brightest\nWhat you need is the fight to be",
            "'Cause when you fight your fears\nYou're pushing on cause only time reveals\nYou're working days until the nights are real\nYou gotta be free\nLive free",
            "You better run towards the sun\nChase what you know\nTrust in your heart\nWe'll make it home\nRun towards the sun\nChase what you know\nTrust in your heart\nWe'll make it home",
            "You wanna get out\nYou want more to see\nAll this you've been dreaming of\nGet lost in the sound\nAnd you will be free",
            "'Cause when you fight your fears\nYou're pushing on cause only time reveals\nYou're working days until the nights are real\nYou gotta be free\nLive free",
            "You better run towards the sun\nChase what you know\nTrust in your heart\nWe'll make it home\nRun towards the sun\nChase what you know\nTrust in your heart\nWe'll make it home",
            "You know it\nYou know it all\nYou know it\nYou give me purpose",
        ]
        embed = Embed(
            color=await ctx.embed_colour(),
            title="Obtaining your API key for Travitia.",
            description=choice(purpose),
        )

        embed.add_field(
            name="Step 1",
            value="Join the Travitia server: https://discord.gg/s4fNByu",
            inline=False,
        )
        embed.add_field(name="Step 2", value="Go to #playground and use `> api`.", inline=False)
        embed.add_field(
            name="Step 3",
            value=(
                "Follow bot's instruction, please add you're using a redbot and Predeactor's cog."
            ),
            inline=False,
        )
        embed.add_field(
            name="Step 4",
            value="Use `[p]set api travitia api_key <Your token>`.\nYou can now use Cleverbot.",
            inline=False,
        )
        embed.add_field(
            name="Note",
            value="We have life, Adrian (Host of Cleverbot's API) doesn't have all of his time just for this API, so don't ask him when he will approve you. PLEASE!",
            inline=False,
        )

        embed.set_footer(text="Purpose - Rhodz", icon_url="https://i.imgur.com/1EiuQLS.png")

        await ctx.send(embed=embed)


def apicheck():
    """
    Check for hidding commands if the API key is not registered.
    Taken from
    https://github.com/PredaaA/predacogs/blob/75a2d0e2561da8f3415e0859c9f540794e6a72b4/nsfw/core.py#L200
    """

    async def predicate(ctx: commands.Context):
        global seems_ok
        if seems_ok is not None:
            return seems_ok
        travitia_keys = await ctx.bot.get_shared_api_tokens("travitia")
        not_key = travitia_keys.get("api_key") is None
        if ctx.invoked_with == "help" and not_key:
            seems_ok = False
            return seems_ok
        if not_key:
            seems_ok = False
            raise commands.UserFeedbackCheckFailure(
                "The API key is not registered, the command is unavailable."
            )
        seems_ok = True
        return seems_ok

    return commands.check(predicate)
