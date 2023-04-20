"""
MIT License

Copyright (c) 2018-2020 crrapi                                                (Note: User deleted)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from enum import Enum

from aiohttp import ClientSession, ContentTypeError


API_URL = "https://public-api.travitia.xyz/talk"


class Emotion(Enum):
    """Enum used to pass an emotion to the API."""

    neutral = "neutral"
    normal = "neutral"
    sad = "sadness"
    sadness = "sadness"
    fear = "fear"
    scared = "fear"
    joy = "joy"
    happy = "joy"
    anger = "anger"
    angry = "anger"


class APIDown(Exception):
    """API is down."""


class InvalidKey(Exception):
    """API key invalid."""


class DictContext:
    """Context for API requests."""

    def __init__(self):
        self._storage = {}

    def update_context(self, id_: int, to_append: str):
        """Pushes data to the Context.

        If the context will contain more than 2 queries, the oldest query will be automatically
        deleted since this is an API limitation.
        """
        if id_ not in self._storage:
            self._storage[id_] = [to_append]
        ctx = self._storage[id_]
        ctx.append(to_append)
        if len(self._storage[id_]) > 2:
            # Remove first query
            ctx.pop(0)

    def get_query_for_api(self, id_: int, query: str):
        """
        Return a dict with the context and query.
        """
        if id_ not in self._storage:
            self._storage[id_] = []
        ctx = {"text": query}
        if self._storage[id_]:
            ctx["context"] = self._storage[id_]
        return ctx


class Response:
    """
    Represents a response from a successful bot query.
    You do not make these on your own, you usually get them from `ask()`.
    """

    def __init__(self, text, status):
        self.text = text
        self.status = status

    def __str__(self):
        return self.text

    @classmethod
    def from_raw(cls, data):
        """Creates a Response from raw data"""
        try:
            return cls(data["response"], data["status"])
        except KeyError:
            raise APIDown("The API did not return a response.")


class Cleverbot:
    """The client to use for API interactions."""

    def __init__(self, api_key: str, session: ClientSession = None, context: DictContext = None):
        if not isinstance(context, DictContext):
            context = DictContext()
        self.context = context
        self.session = session if isinstance(session, ClientSession) else ClientSession()
        self.api_key = api_key  # API key for the Cleverbot API

    async def ask(self, id_: int, query: str, *, emotion: Emotion = Emotion.neutral):
        """Queries the Cleverbot API."""

        ctx = self.context.get_query_for_api(id_, query)
        self.context.update_context(id_, query)

        ctx["emotion"] = emotion.value if isinstance(emotion, Emotion) else Emotion.neutral.value

        async with self.session.post(
            API_URL, data=ctx, headers={"authorization": self.api_key}
        ) as req:
            try:
                resp = await req.json()
            except ContentTypeError:
                raise APIDown(
                    "The API is currently not working. Please wait while the devs fix it."
                )

            if resp.get("error") == "Invalid authorization credentials":
                raise InvalidKey("The API key you provided was invalid.")

            if resp.get("response") == "The server returned a malformed response or it is down.":
                raise APIDown(
                    "The API is currently not working. Please wait while the devs fix it."
                )

        return Response.from_raw(resp)

    async def close(self):
        """Closes the session."""
        if self.session:
            await self.session.close()
