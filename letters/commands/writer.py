from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import sleep
from typing import Optional

from discord.ext.commands.errors import ArgumentParsingError, UserNotFound
from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, escape, inline, underline
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate

from ..abc import MixinMeta
from ..classes import Letter
from ..errors import NeedCHPostal
from .menu import TemplateMenu, TemplatePage

TEMPLATES = [
    "Dear $receiver,\n\n$message\n\nSincerely,\n$authors.",
    "Dear $receiver,\n\n$message\n\nFrom your friend(s),\n$authors.",
    "To $receiver,\n\n$message\n\nFrom $authors.",
]
CH_POSTAL_COMPANY_INVITE = "https://discord.gg/FPfNvTeQvn"
REPOSITORY_LINK = "https://github.com/Predeactor/Predeactor-Cogs"
RED_ID = 133049272517001216


class Writer(MixinMeta):
    async def send_letter(self, ctx: commands.Context, letter: Letter):
        starting = bold("\N{HOURGLASS}\N{VARIATION SELECTOR-16} Starting sending process...")
        msg = await ctx.send(starting)
        for user_info in letter.receivers.items():
            await sleep(7.5)
            sending = "\n" + bold(
                "{emoji} Sending letter to {user}...".format(
                    emoji="\N{HOURGLASS}\N{VARIATION SELECTOR-16}", user=user_info[1]
                )
            )
            sent = "\n" + "{emoji} Sent letter to {user}.".format(
                emoji="\N{WHITE HEAVY CHECK MARK}", user=user_info[1]
            )
            failed = "\n" + "{emoji} Failed to send letter to {user}.".format(
                emoji="\N{NO ENTRY SIGN}", user=user_info[1]
            )
            new: str = msg.content + sending
            await msg.edit(content=new)
            letter_id = await self.add_new_letter_in_letterbox(int(user_info[0]), letter)
            was_done = await self.alert_new_letter(int(user_info[0]), letter, letter_id)
            new = msg.content.replace(sending, sent if was_done else failed)
            await msg.edit(content=new)
        new = msg.content.replace(starting, underline("Finished."))
        await msg.edit(content=new)

    async def wait_for_message(self, ctx: commands.Context, content: str):
        msg = await ctx.send(content)
        pred = MessagePredicate.same_context(ctx)
        try:
            message = await self.bot.wait_for("message", check=pred, timeout=60)
        except AsyncTimeoutError:
            return None
        finally:
            await msg.delete()
        return message.content

    async def confirm(self, ctx: commands.Context, content: str):
        msg = await ctx.send(content)
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=60)
        except AsyncTimeoutError:
            return None
        finally:
            await msg.delete()
        return pred.result

    async def ask_for_receivers(self, ctx: commands.Context) -> Optional[dict]:
        # ask if know to who to send to
        result = await self.confirm(
            ctx, "Do you know the IDs/names of the persons I must contact?"
        )
        if result is False:
            raise NeedCHPostal()
        # ask for id
        message = (
            "Please give me the name, mention, or ID of the persons you want to send a letter "
            "to.\n\nThis need to be separated with a command, for example:\n"
            + inline("131813999326134272, Violet Evergarden, MAX#1000")
            + "\nNote: I may not be able to find the user if you don't give me their ID."
        )

        answer = await self.wait_for_message(ctx, message)
        if answer is None:
            raise AsyncTimeoutError()
        ids = list(map(lambda x: x.strip(), answer.split(",", maxsplit=5)))
        if len(ids) > 5:
            raise ArgumentParsingError("Too many users given.")
            # It's nice to require CH services, but eh, would be nice if we don't have too much work lol
        found = []
        for user in ids:
            try:
                possible_user = await commands.UserConverter().convert(ctx, user)
                if not possible_user.bot:  # We can't DM bot
                    found.append(possible_user)
            except UserNotFound:
                continue
        if not found:
            await ctx.send("I found nobody! Try again...")
            return None

        # check if valid
        msg = "I have found the following users, are they the correct users?\n" + "\n".join(
            f"- {escape(str(user), mass_mentions=True, formatting=True)}" for user in found
        )
        result = await self.confirm(ctx, msg)
        if not result:
            if result is not None:  # It is False
                await ctx.send(
                    "Try again, if you want a more precise selection, use their ID instead of their name, or "
                    " you can join CH Postal Company: ||<{invite}>||.".format(
                        invite=CH_POSTAL_COMPANY_INVITE
                    )
                )
            return None

        # check if can be contacted
        can_be_contacted = []
        async for guild in AsyncIter(self.bot.guilds, steps=100):
            for user in found:
                if user in guild.members:
                    can_be_contacted.append(user)
        return {
            "users": {user.id: user.name for user in can_be_contacted},
            "missing_contactable": [user for user in found if user not in can_be_contacted],
        }

    @commands.command(name="write")
    @commands.max_concurrency(1, per=commands.BucketType.user)
    async def write_letter(self, ctx: commands.Context):
        """
        Write a letter.
        """
        # try:
        await self.go_for_letter(ctx)
        # except Exception:
        #     await ctx.send(
        #         error(
        #             "An unexpected error happened while writing your letter!\nPlease report "
        #             f"this issue to {REPOSITORY_LINK}."
        #         )
        #     )

    async def go_for_letter(self, ctx: commands.Context):
        try:
            receivers = await self.ask_for_receivers(ctx)
        except AsyncTimeoutError:
            await ctx.send("Feel free to ask me another day!")
            return
        except ArgumentParsingError:
            await ctx.send("I can't send a letter to more than 5 persons, sorry!")
            return
        except NeedCHPostal:
            await ctx.send(
                "If so, you'll require the help from CH Postal Company, you can contact them by "
                "joining this server: " + CH_POSTAL_COMPANY_INVITE
            )
            return
        if not receivers:
            return
        if receivers["missing_contactable"]:
            await ctx.send(
                "It looks like I will be unable to contact those users:\n"
                + "\n".join(
                    f"- {escape(str(user), mass_mentions=True, formatting=True)}"
                    for user in receivers["missing_contactable"]
                )
                + (
                    "\nIf you want to try to contact those users, you can try to join CH Postal "
                    f"Company: ||<{CH_POSTAL_COMPANY_INVITE}>||"
                )
            )
            return
        # noinspection PyTypeChecker
        template = await TemplateMenu(TemplatePage(TEMPLATES)).prompt(ctx)
        if not template:
            await ctx.send("Let's write another letter another time.")
            return
        message = (
            "Alright, it's time to write the message in your letter...\n\nNow, you must "
            "send me the content of your letter, the message that will replace "
            f"{inline('$message')} in the template.\n\nFor that, I'm giving you 15 minutes "
            "to write it. In case you don't finish in time, you will need to redo "
            "the command...\n\nNow listening for the letter's message!"
        )
        letter_message = await self.wait_for_message(ctx, message)

        letter = Letter(
            {ctx.author.id: ctx.author.name}, receivers["users"], template, letter_message
        )
        await ctx.send(letter.write_letter("$receiver")[:2000], delete_after=60)
        result = await self.confirm(
            ctx, bold("Here is a copy of your letter, do you want me to send it?")
        )
        if not result:
            await ctx.send("Not sending the letter...")
            return
        await self.send_letter(ctx, letter)
