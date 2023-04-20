from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import sleep

from redbot.core import commands
from redbot.core.utils.chat_formatting import bold, pagify, underline
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from ..abc import MixinMeta
from ..classes import Letter


class LetterBox(MixinMeta):
    @commands.group(name="letterbox")
    async def letterbox(self, ctx: commands.Context):
        """
        Read letters, manage your letterbox.
        """
        pass

    @letterbox.command(name="read")
    async def read_letter(self, ctx: commands.Context, letter_id: str):
        """
        Read a letter.

        letter_id is the ID of the letter you want to read.
        """
        letters = await self.config.custom("LetterBox", ctx.author.id).letterbox()
        if letter_id not in letters:
            await ctx.send("This letter does not exist in your letterbox!")
        letter = Letter.from_json(letters[letter_id])
        content = letter.write_letter(ctx.author.name)
        if not letter.was_read:
            msg = await ctx.send("Sure! Let me write it... Just a moment...")
            async with ctx.typing():
                await sleep(len(content) * 0.01)
            await msg.delete()
            await sleep(1)
        for text in pagify(content):
            await ctx.send(text)
        await self.config.custom("LetterBox", ctx.author.id).letterbox.set_raw(
            letter_id, "was_read", value=True
        )

    @letterbox.command(name="list")
    async def list_letters(self, ctx: commands.Context):
        """
        List your letters in your letterbox.
        """
        letters = await self.config.custom("LetterBox", ctx.author.id).letterbox()
        if not letters:
            await ctx.send("You don't have any letters in your letterbox!")
            return
        for text in pagify(self.format_list(letters)):
            await ctx.send(text)

    @letterbox.command(name="delete", aliases=["del"])
    async def delete_letter(self, ctx: commands.Context, letter_id: str):
        """
        Delete a specific letter.
        """
        letters = await self.config.custom("LetterBox", ctx.author.id).letterbox()
        if letter_id not in letters:
            await ctx.send("This letter is not in your letterbox.")
            return
        msg = await ctx.send(
            bold(
                "Are you sure you want to delete this letter? You "
                + underline("won't be")
                + " able to recovere this letter afterwards.",
                escape_formatting=False,
            )
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=60)
        except AsyncTimeoutError:
            return None
        if pred.result:
            await self.config.custom("LetterBox", ctx.author.id).letterbox.clear_raw(letter_id)
            await msg.edit(content="Deleted your letter.")
        else:
            await msg.edit(content="I won't touch it then!")

    @letterbox.group(name="archive")
    async def archive(self, ctx: commands.Context):
        """
        Manage your archive.

        Archive is where you can keep letters outside of your letterbox.
        """
        pass

    @archive.command(name="add")
    async def add_to_archive(self, ctx: commands.Context, letter_id: str):
        """
        Add a letter to your archive.
        """
        infos = await self.config.custom("LetterBox", ctx.author.id).all()
        if not infos["letterbox"]:
            await ctx.send("You don't have any letters in your letterbox!")
            return
        if letter_id not in infos["letterbox"]:
            await ctx.send("This letter is not in your letterbox!")
            return
        if letter_id in infos["archive"]:
            await ctx.send("This letter is already in your letterbox!")
            return
        letter = infos["letterbox"][letter_id]
        infos["archive"][letter_id] = letter
        del infos["letterbox"][letter_id]
        await self.config.custom("LetterBox", ctx.author.id).set(infos)
        await ctx.send("Moved your letter in your archives!")

    @archive.command(name="remove")
    async def remove_from_archive(self, ctx: commands.Context, letter_id: str):
        """
        Add a letter to your archive.
        """
        infos = await self.config.custom("LetterBox", ctx.author.id).all()
        if not infos["archive"]:
            await ctx.send("You don't have any letters in your archives!")
            return
        if letter_id not in infos["archive"]:
            await ctx.send("This letter is not in your archives!")
            return
        letter = infos["archive"][letter_id]
        infos["letterbox"][letter_id] = letter
        del infos["archive"][letter_id]
        await self.config.custom("LetterBox", ctx.author.id).set(infos)
        await ctx.send("Moved your letter in your letterbox!")

    @archive.command(name="list")
    async def list_archive(self, ctx: commands.Context):
        """
        List your letters in your archive.
        """
        archive = await self.config.custom("LetterBox", ctx.author.id).archive()
        if not archive:
            await ctx.send("You don't have any letters in your archive!")
            return
        for text in pagify(self.format_list(archive, add_was_read=False)):
            await ctx.send(text)
