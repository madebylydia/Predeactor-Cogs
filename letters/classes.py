from string import Template
from typing import Dict

from redbot.core.utils.chat_formatting import humanize_list


class Letter:
    """
    Represent a letter.
    """

    def __init__(
        self,
        authors: Dict[int, str],
        receivers: Dict[int, str],
        template: str,
        message: str,
        *,
        was_read: bool = False,
    ):

        # Authors
        self.author = authors[next(iter(authors))]  # Name of the first original author
        self.authors = authors

        self.receivers = receivers

        self.message = message
        self.template = template
        self.was_read = was_read

    def write_letter(self, receiver_name: str) -> str:
        return Template(self.template).safe_substitute(
            receiver=receiver_name,
            message=self.message,
            authors=humanize_list(list(self.authors.values())),
        )

    def to_json(self) -> dict:
        return {
            "author": self.author,
            "authors": self.authors,
            "receivers": self.receivers,
            "template": self.template,
            "message": self.message,
            "was_read": self.was_read,
        }

    @classmethod
    def from_json(cls, json: dict):
        return cls(
            authors=json["authors"],
            receivers=json["receivers"],
            template=json["template"],
            message=json["message"],
            was_read=json["was_read"],
        )
