from typing import Union

import discord
from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box, humanize_list
from tabulate import tabulate

from .abc import CompositeMetaClass
from .classes import Letter
from .commands import LetterBox, LetterSet, Writer

# Sorry Trusty, but I like to :aha:
from .errors import LetterNotExist, StopService

DEFAULT_USER = {"stop": False, "first_usage": True, "blocklist": []}
DEFAULT_LETTERBOX = {"letterbox": {}, "archive": {}, "next_id": 1}


class Letters(Writer, LetterSet, LetterBox, commands.Cog, metaclass=CompositeMetaClass):
    """
    Send a letter to someone.
    """

    def __init__(self, bot, *_args):
        super().__init__(*_args)
        self.bot = bot
        self.config = Config.get_conf(self, identifier=27032020, force_registration=True)
        self.config.register_user(**DEFAULT_USER)

        self.config.init_custom("LetterBox", 1)
        self.config.register_custom("LetterBox", **DEFAULT_LETTERBOX)

    @staticmethod
    def format_list(letters: dict, *, add_was_read: bool = True):
        if not letters:
            return str()
        headers = ["ID", "Author"]
        if add_was_read:
            headers.append("Was read")
        letters_list = []
        for letter in letters.items():
            letter_info = [str(letter[0]), letter[1]["author"]]
            if add_was_read:
                letter_info.append("Yes" if letter[1]["was_read"] else "No")
            letters_list.append(letter_info)
        msg = tabulate(letters_list, headers=headers, tablefmt="github")
        return box(msg)

    async def alert_new_letter(self, user_id: int, letter: Letter, letter_id: int):
        user = self.bot.get_user(user_id)
        if user is None:  # User not found
            raise discord.NotFound("User cannot be contacted.")
        if not await self.allow_service(user):
            raise StopService("User stopped using the service.")
        message = str()
        prefix = await self.bot._config.prefix()
        first_time = await self.config.user(user).first_usage()
        if first_time:
            message += (
                (
                    f"Hello {user.name}, this is the first time you're receiving a letter in your "
                    "letterbox, so let me introduce you to the service.\n\nLetters is a service that "
                    "allows you to send and receive letters from members of Discord, as long as I "
                    "share a server with you and I can contact you. When you receive a letter, the "
                    "letter gets into your letterbox where all your letters are stored, so you can "
                    "open a letter whenever you want. When you have read a letter, it is marked as "
                    "read.\n\nYou can disable this service. **However, this system is meant for "
                    "receiving letters over Discord from others, from your friends, from the past or "
                    "of today, every letter deserves to be delivered.** It would be hurtful "
                    "for you to disable it.\n\n Now that you are familiar with the concept, here are "
                    "2 commands you should know:\n- `[p]letterbox` to check your letterbox;\n- "
                    "`[p]letterset` to set your settings for the letter service;\n\n You will not "
                    "receive this message again. From now on, you will only receive regular alerts "
                    "about new letters.\n\n📩 You have received a new letter from {authors}! Check "
                    "it out in your letterbox!"
                )
                .format(authors=humanize_list(list(letter.authors.values())))
                .replace("[p]", prefix[0])
            )
        else:
            message += (
                f"📩 You have received a new letter from {letter.author}! Check it out in your "
                "letterbox! (`[p]letterbox`)"
            ).replace("[p]", prefix[0])
            if [
                i
                for i in list(letter.authors.values())
                if i in await self.config.user(user).blocklist()
            ]:
                message += (
                    "\n⚠ The author of this letter has been marked as blocked, this "
                    "letter will still go to your letterbox, open it if you want or delete "
                    "it. Letter ID: " + str(letter_id)
                )
        try:
            await user.send(message)
            if first_time:
                await self.config.user(user).first_usage.set(False)
            return True
        except discord.HTTPException:
            return False

    async def add_new_letter_in_letterbox(self, receiver_id: int, letter: Letter) -> int:
        """
        Append a new letter to a letterbox.
        """
        user = self.bot.get_user(receiver_id)
        if user is None:  # User not found
            raise discord.NotFound("User cannot be found.")
        if not await self.allow_service(user):
            raise StopService("User stopped using the service.")
        letter_id = await self.config.custom("LetterBox", user.id).next_id()
        await self.config.custom("LetterBox", user.id).letterbox.set_raw(
            str(letter_id), value=letter.to_json()
        )
        await self.config.custom("LetterBox", user.id).next_id.set(letter_id + 1)
        return letter_id

    async def get_letter_in_letterbox(self, user_id: int, letter_id: int) -> Letter:
        user_letterbox = await self.config.user_from_id(user_id).letterbox()
        try:
            letter = user_letterbox[str(letter_id)]
        except KeyError:
            raise LetterNotExist("Cannot find the letter ID.")
        return Letter.from_json(letter)

    async def delete_letter_in_letterbox(self, receiver_id: int, letter_id: int):
        """
        Remove a new letter to a letterbox.
        """
        user = await self.bot.get_or_fetch_user(receiver_id)
        if user is None:  # User not found
            raise discord.NotFound("User cannot be found.")
        async with self.config.user(user).letterbox() as user_letterbox:
            try:
                del user_letterbox[str(letter_id)]
            except KeyError:
                raise LetterNotExist("Cannot find the letter ID.")

    async def allow_service(self, user: Union[discord.User, int]):
        if user is int:
            user = self.bot.get_user(user)
            if not user:  # User not found
                raise discord.NotFound("User cannot be found.")
        stopped = await self.config.user(user).stop()
        return not stopped
