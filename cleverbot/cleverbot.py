import asyncio
import logging

from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate

from .core import Core, apicheck

log = logging.getLogger("predeactor.cleverbot")


class CleverBot(Core):
    """Ask questions to Cleverbot or even start a Conversation with her!"""

    @apicheck()
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ask(self, ctx: commands.Context, *, question: str):
        """Ask an unique question to Cleverbot.

        You won't have a discussion with Cleverbot, you're just
        asking a single question."""
        async with ctx.typing():
            session = await self._make_cleverbot_session()
            answer, answered = await self.ask_question(session, question, ctx.author.id)
            if answered:
                message = "{user}, {answer}".format(user=ctx.author.name, answer=answer)
            else:
                message = answer
            await session.close()
            await ctx.send(message)

    @apicheck()
    @commands.command()
    async def conversation(self, ctx: commands.Context):
        """Start a conversation with Cleverbot
        You don't need to use a prefix or the command using this mode."""

        if ctx.author.id in self.conversation:
            await ctx.send("There's already a conversation running. Say `close` to stop it.")
            return

        session = await self._make_cleverbot_session()
        self.conversation[ctx.author.id] = {
            "session": session,
            "task": None,
        }

        # Handled when the cog is restarted/unloaded, which we will let the user know.

        await ctx.send(
            "Starting a new Cleverbot session!\n\nSay `close` to stop the conversation"
            " with me !\n\nYour conversation will be automatically closed if CleverBot"
            " receive no answer.\nThis conversation is only available in this channel."
        )

        prefixes = tuple(await self.bot.get_valid_prefixes())

        try:
            while True:
                self.conversation[ctx.author.id]["task"] = task = asyncio.Task(
                    self.bot.wait_for(
                        "message", check=MessagePredicate.same_context(ctx), timeout=300
                    )
                )
                try:
                    message = await task.get_coro()  # Wait for user message...
                except asyncio.TimeoutError:
                    await ctx.send(
                        "You haven't answered me! \N{PENSIVE FACE}\nI'm closing our session..."
                    )
                    break
                except asyncio.CancelledError:
                    await ctx.send("Our session has been cancelled due to cog unload! Closing...")
                    break
                if message.content.startswith(prefixes):
                    continue
                if message.content.lower() in ("close", "c"):
                    await ctx.send("Alright, bye then. \N{WAVING HAND SIGN}")
                    break
                async with ctx.typing():
                    answer, answered = await self.ask_question(
                        session, message.content, message.author.id
                    )
                await message.reply(answer)
                if not answered:
                    break
                continue
        finally:
            await self.conversation[ctx.author.id]["session"].close()
            del self.conversation[ctx.author.id]

    def cog_unload(self):
        for session in self.conversation.values():
            if session["task"]:
                session["task"].cancel()
                # The session is closed automatically by the 'finally" block at the end of the cmd
