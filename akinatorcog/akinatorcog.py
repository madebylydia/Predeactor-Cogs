import asyncio
from json import JSONDecodeError
from typing import Optional
from traceback import format_exception

import discord
from akinator import AkiNoQuestions, CantGoBackAnyFurther, InvalidLanguageError
from akinator.async_aki import Akinator as Aki
from akinator.utils import get_lang_and_theme
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.predicates import MessagePredicate

from .checks import need_child_mode, testing_check

__author__ = ["Predeactor"]
__version__ = "Beta v0.8.3"
NOTICE = (
    'To answer a question, you can use the following terms:\n- "yes" OR "y" OR "0" for answering '
    '"Yes".\n- "no" OR "n" OR "1" for answer "No".\n- "i" OR "idk" OR "i dont know" OR "i don\'t '
    'know" OR "2" for answer "I don\'t know".\n- "probably" OR "p" OR "3" for answering '
    '"Probably".\n- "probably not" OR "pn" OR "4" for answering "Probably not".\n\nYou can also '
    'say "b" or "back" to change your last question.'
)
ANSWERS = [
    "yes",
    "y",
    "no",
    "n",
    "i",
    "idk",
    "i don't know",
    "i dont know",
    "probably",
    "p",
    "probably not",
    "pn",
    "0",
    "1",
    "2",
    "3",
    "4",
    "b",
    "back",
]
BACK_ANSWERS = (
    "back",
    "b",
)


_ = Translator("Akinator", __file__)


@cog_i18n(_)
class Akinator(commands.Cog, name="Akinator"):
    """
    The genius, Akinator, will guess your mind and find who you are thinking of, go challenge him!
    """

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(self, 151546841564168412, True)
        self.config.register_global(version=0)
        self.__error = None
        self.ongoing_games = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        This will put some text at the top of the main help. ([p]help Akinator)
        Thank to Sinbad.
        """
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nVersion: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(__author__),
            version=__version__,
        )

    @commands.group(aliases=["aki"])
    @testing_check()
    async def akinator(self, ctx: commands.Context):
        """
        Answer Akinator's question and get challenged!
        """
        pass

    @akinator.command()
    async def start(self, ctx: commands.Context, *, locale: str = None):
        """
        Start a session with Akinator.
        """
        if ctx.author.id in self.ongoing_games:
            await ctx.send(_("You're already running a game!"))
            return
        await ctx.send(NOTICE)
        locale = await self.ask_for_locale(ctx, locale)

        try:
            self.ongoing_games[ctx.author.id] = {
                "creating": True  # Just to know if 2 commands are being executed & reduce errors.
            }
            await self.game_with(ctx, locale)
        except asyncio.CancelledError:
            # Command has been cancelled. (Or user didn't answer)
            pass
        except JSONDecodeError as e:
            self.__error = format_exception(type(e), e, e.__traceback__)
            await ctx.bot.send_to_owners(
                "Hello, This is your Captain's speaking, Akinator's Cog Creator.\nIt seems your "
                "bot catched an error I'm interested in and that annoys me a bit, since it's "
                "somewhat hard to reproduce, could you please contact me? I am {pred} on Discord."
                "\nThanks.\nIf this error keep spamming, unload and contact me."
            )
        finally:
            del self.ongoing_games[ctx.author.id]

    @akinator.command()
    async def cancel(self, ctx: commands.Context):
        """Cancel your game with Akinator."""
        if ctx.author.id not in self.ongoing_games:
            await ctx.send(_("You're not running any game!"))
            return
        self.ongoing_games[ctx.author.id]["task"].cancel()
        await ctx.tick()

    async def game_with(self, ctx: commands.Context, locale: str, *, needed_progression: int = 80):

        my_akinator = Aki()
        self.ongoing_games[ctx.author.id] = {
            "akinator": my_akinator,
            "author": ctx.author,
            "channel": ctx.channel,
            "task": None,
        }
        await ctx.trigger_typing()
        next_question = await my_akinator.start_game(
            language=locale, child_mode=need_child_mode(ctx.channel)
        )

        question_count = await self.continuous_question(
            my_akinator, needed_progression, ctx, next_question
        )

        # Time to reveal answer.
        await my_akinator.win()
        possible_edit = await ctx.send(
            embed=self.make_guess_embed(
                await ctx.embed_colour(), question_count, my_akinator, ctx.author
            )
        )
        aki_won = await self.ask_if_aki_won(ctx, possible_edit)
        if not aki_won:
            await ctx.send(
                "Better luck next time, I guess... \N{SMILING FACE WITH OPEN MOUTH AND COLD SWEAT}"
            )
        else:
            await ctx.send(
                "Of course I won! I always guess exactly! \N{FACE WITH PARTY HORN AND PARTY HAT}"
            )

    async def continuous_question(
        self,
        akinator: Aki,
        requested_progression: int,
        ctx: commands.Context,
        next_question: str,
        *,
        max_question: int = 79,
    ) -> int:
        need_questions = True
        question_count = 1
        while need_questions or (max_question == question_count):
            infos = {
                "game": self.ongoing_games[ctx.author.id],
                "count": question_count,
                "question": _("Question {count}: {question}").format(
                    count=question_count, question=next_question
                ),
            }
            user_input = await self.send_and_ask_question(**infos)
            # We technically should have something correct
            try:
                async with ctx.typing():
                    if user_input in BACK_ANSWERS:
                        try:
                            next_question = await akinator.back()
                        except CantGoBackAnyFurther:
                            await ctx.send(
                                _("Oops! Can't go back! You need to answer my question!")
                            )
                            continue
                    else:
                        try:
                            next_question = await akinator.answer(user_input)
                        except JSONDecodeError:
                            try:
                                next_question = await akinator.answer(user_input)
                            except JSONDecodeError as e:
                                await ctx.send("I can't answer to Akinator. Server error.")
                                raise e

                    if akinator.progression >= requested_progression:
                        need_questions = False
                    else:
                        question_count += 1
            except AkiNoQuestions:
                await ctx.send("Oops! Reached 80 questions! That's an issue! Trying to win...")
                await akinator.back()
                break
        return question_count

    async def ask_if_aki_won(self, ctx: commands.Context, possible_edit: discord.Message):
        pred = MessagePredicate.yes_or_no(ctx)
        task = asyncio.Task(
            self.bot.wait_for(
                "message",
                check=pred,
                timeout=60,
            )
        )
        # I have no idea if it's good to do that lmao
        self.ongoing_games[ctx.author.id]["task"] = task
        try:
            await task.get_coro()
        except asyncio.TimeoutError:
            await possible_edit.edit(
                content="You haven't answered me... Think about it next time. \N{PENSIVE FACE}"
            )
            raise asyncio.CancelledError()  # Why not?
        except asyncio.CancelledError as exception:
            await possible_edit.edit(content="Successfully cancelled. \N{RELIEVED FACE}")
            raise exception
        return pred.result

    async def send_and_ask_question(self, game: dict, count: int, question: str) -> str:
        possible_edit = await game["channel"].send(question)
        task = asyncio.Task(
            self.bot.wait_for(
                "message",
                check=MessagePredicate.lower_contained_in(
                    collection=ANSWERS, user=game["author"], channel=game["channel"]
                ),
                timeout=300,
            )
        )
        # I have no idea if it's good to do that lmao
        self.ongoing_games[game["author"].id]["task"] = task
        try:
            result = await task.get_coro()
        except asyncio.TimeoutError:
            await possible_edit.edit(
                content="You haven't answered me... Think about it next time. \N{PENSIVE FACE}"
            )
            raise asyncio.CancelledError()  # Why not?
        except asyncio.CancelledError as exception:
            await possible_edit.edit(content="Successfully cancelled. \N{RELIEVED FACE}")
            raise exception
        return result.content

    @staticmethod
    def make_guess_embed(
        bot_color: discord.Color, count: int, akinator: Aki, author: discord.User
    ):
        embed = discord.Embed(
            color=bot_color,
            title=_("Hmm... I think I've guessed..."),
            description=_("Is it {name}? Did I win? The description is {desc}.").format(
                name=akinator.first_guess["name"],
                desc=akinator.first_guess["description"],
            ),
        )
        embed.set_image(url=akinator.first_guess["absolute_picture_path"])
        embed.set_footer(
            icon_url=author.avatar_url,
            text=(
                _("Game running for {name}. I asked over {num} questions! (Cog version {ver})")
            ).format(name=author.name, num=str(count), ver=__version__),
        )
        return embed

    # Locale util

    async def ask_for_locale(self, ctx: commands.Context, locale: Optional[str] = None) -> str:
        if not locale:
            await ctx.send(
                _(
                    "Do you wish to set a specific language? If so, please specify it now (Find "
                    "all available language at "
                    "<https://github.com/NinjaSnail1080/akinator.py#functions>) else just say "
                    "'no'."
                )
            )
            try:
                res = await self.bot.wait_for(
                    "message", timeout=60, check=MessagePredicate.same_context(ctx=ctx)
                )
            except asyncio.TimeoutError:
                raise commands.UserFeedbackCheckFailure(
                    _("You didn't answered in time... \N{PENSIVE FACE}")
                )
            locale = res.content.lower() if res.content not in ("no", "n") else None
        else:
            locale = "en"
        self.ensure_valid_locale(locale)
        return locale

    @staticmethod
    def ensure_valid_locale(locale: Optional[str] = None) -> None:
        if locale:  # We check the locale is correct before all
            try:
                get_lang_and_theme(locale)
            except InvalidLanguageError:
                raise commands.UserFeedbackCheckFailure("Incorrect locale/language given.")

    async def _killer(self, bot):
        if await self.config.version() == 0:
            THE_GRAND_FINAL = (
                "Heya! Don't wanna be ya! :D\nThis is your Captain' speaking.\n"
                "I release today the death of my Akinator cog on my repo, that said, this cog is "
                "now unsupported. If you wonder why, it's because this cog has been quite "
                "problematic to me, as a cog creator and the feeling in opening my repo. Really, "
                "I hated this cog and still do.\nIf you want an alternative, Phenom4n4n made one, "
                "available here: https://github.com/Phenom4n4n/phen-cogs\nThis was your Captain "
                "speaking, over."
            )
            await bot.send_to_owners(THE_GRAND_FINAL)
            await self.config.version.set(1)
