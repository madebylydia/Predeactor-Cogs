from abc import ABC, abstractmethod
from typing import Union

from discord import User
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from .classes import Letter


class MixinMeta(ABC):
    def __init__(self, *_args):
        self.bot: Red
        self.config: Config

    @staticmethod
    @abstractmethod
    def format_list(letters: dict, *, add_was_read: bool = True):
        raise NotImplementedError()

    @abstractmethod
    async def alert_new_letter(self, user_id: int, letter: Letter, letter_id: int):
        raise NotImplementedError()

    @abstractmethod
    async def add_new_letter_in_letterbox(self, receiver_id: int, letter: Letter) -> int:
        raise NotImplementedError()

    @abstractmethod
    async def get_letter_in_letterbox(self, user_id: int, letter_id: int) -> Letter:
        raise NotImplementedError()

    @abstractmethod
    async def delete_letter_in_letterbox(self, receiver_id: int, letter_id: int):
        raise NotImplementedError()

    @abstractmethod
    async def allow_service(self, user: Union[User, int]):
        raise NotImplementedError()


class CompositeMetaClass(type(Cog), type(ABC)):
    """
    Allows the metaclass used for proper type detection to coexist with discord.py's metaclass.
    Credit to https://github.com/Cog-Creators/Red-DiscordBot (mod cog) for all mixin stuff.
    Credit to the top of the file "base.py".
    """

    pass
