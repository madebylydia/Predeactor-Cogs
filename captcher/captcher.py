import asyncio

import discord
from redbot.core import checks, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import MessagePredicate

from .core import Core


class Captcher(Core):
    @commands.group(name="setcaptcher", alias=["captcherset"])
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def config(self, ctx: commands.GuildContext):
        """
        Configure settings for Captcher.
        """
        pass

    @config.command()
    async def settings(self, ctx: commands.Context):
        """Show settings for your guild."""
        params = {
            "autorole": "Automatic role to give",
            "temprole": "Temporary role to give through verification",
            "verifchannel": "Channel to send captcha",
            "logschannel": "Channel to logs actions",
            "active": "Captcher activated",
        }
        settings = await self.data.guild(ctx.guild).all()
        message = ""
        for setting in settings.items():
            parameter = params[setting[0]]
            rawvalue = setting[1]
            value = rawvalue
            if setting[0] in ("verifchannel", "logschannel"):
                value = f"<#{rawvalue}>"  # Channel mention.
            if setting[0] in ("autorole", "temprole"):
                value = f"<@&{rawvalue}>"  # Role mention, but don't worry, bot won't ping.
            if rawvalue is None:
                value = "Not set."
            message += "{param}: {val}\n".format(param=parameter, val=value)
        await ctx.send(message, allowed_mentions=discord.AllowedMentions(roles=False))

    @config.command()
    async def autorole(self, ctx: commands.Context, *, role_to_give: discord.Role = None):
        """
        Give a role when the user successfully completed the captcha.

        If a role is already set and you don't provide a role, actual role will
        be deleted.
        """
        if role_to_give is None and await self.data.guild(ctx.guild).autorole():
            await self.data.guild(ctx.guild).autorole.clear()
            await ctx.send("Role configuration removed.")
            return
        if role_to_give:
            if ctx.author.top_role < role_to_give:
                await ctx.send(
                    (
                        "This role is higher than your highest role in the role "
                        "hierarchy, choose another role, ask someone else to use this "
                        "command, or get a higher role."
                    )
                )
                return
            if ctx.me.top_role < role_to_give:
                await ctx.send(
                    (
                        "This role is higher than my highest role in the hierarchy, "
                        "give me an another role, put my role higher or put the role "
                        "lower."
                    )
                )
                return
            await self.data.guild(ctx.guild).autorole.set(role_to_give.id)
            message = "{role.name} will be given when members pass the captcha.".format(
                role=role_to_give
            )
        else:
            await ctx.send_help()
            message = box("There's no role in configuration.")
        await ctx.send(message)

    @config.command()
    async def temprole(self, ctx: commands.Context, *, temporary_role: discord.Role = None):
        """
        Role to give when someone join, it will be automatically removed after
        passing captcha.

        If a role is already set and you don't provide a role, actual role will
        be deleted.
        """
        if temporary_role is None and await self.data.guild(ctx.guild).temprole():
            await self.data.guild(ctx.guild).temprole.clear()
            await ctx.send("Temporary role configuration removed.")
            return
        if not temporary_role:
            await ctx.send_help()
            await ctx.send(box("There's no temporary role in configuration."))
            return
        if temporary_role:
            if ctx.author.top_role < temporary_role:
                await ctx.send(
                    (
                        "This role is higher than your highest role in the role "
                        "hierarchy, choose another role, ask someone else to use this "
                        "command, or get a higher role."
                    )
                )
                return
            if ctx.me.top_role < temporary_role:
                await ctx.send(
                    (
                        "This role is higher than my highest role in the hierarchy, "
                        "give me an another role, put my role higher or put the role "
                        "lower."
                    )
                )
                return
            await self.data.guild(ctx.guild).temprole.set(temporary_role.id)
            await ctx.send(
                (
                    "{role.name} will be given when members start the captcha.".format(
                        role=temporary_role
                    )
                )
            )

    @config.command(alias=["verificationchannel", "verifchan"])
    async def verifchannel(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        """
        Set where the captcha must be sent.
        """
        if channel is None and await self.data.guild(ctx.guild).verifchannel():
            await self.data.guild(ctx.guild).verifchannel.clear()
            await ctx.send("Verification channel configuration removed.")
        if not channel:
            await ctx.send_help()
            await ctx.send(box("There's no verification channel configured."))
            return
        needed_permissions = [
            "manage_messages",
            "read_messages",
            "send_messages",
            "manage_roles",
            "attach_files",
        ]
        perms = self._permissions_checker(needed_permissions, channel)
        if isinstance(perms, str):
            message = perms
        else:
            await self.data.guild(ctx.guild).verifchannel.set(channel.id)
            message = "Channel has been configured."
        await ctx.send(message)

    @config.command(alias=["logchan", "logschan", "logchannel"])
    async def logschannel(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        """
        Set the log channel, really recommended for knowing who passed verification
        or who failed.
        """
        if channel is None and await self.data.guild(ctx.guild).logschannel():
            await self.data.guild(ctx.guild).logschannel.clear()
            await ctx.send("Logging channel configuration removed.")
            return
        if not channel:
            await ctx.send_help()
            await ctx.send(box("There's no logs channel configured"))
            return
        needed_permissions = [
            "read_messages",
            "send_messages",
        ]
        checker = self._permissions_checker(needed_permissions, channel)
        if isinstance(checker, str):
            await ctx.send(checker)
            return  # Missing permission
        await self.data.guild(ctx.guild).logschannel.set(channel.id)
        await ctx.send("{channel.name} will be used for captcha logs.".format(channel=channel))

    @config.command()
    async def activate(self, ctx: commands.Context, true_or_false: bool = None):
        """
        Set if Captcher is activated.
        """
        data = await self.data.guild(ctx.guild).all()
        if true_or_false is not None:
            channel_id = data["verifchannel"]
            fetched_channel = self.bot.get_channel(channel_id)
            if fetched_channel:
                needed_permissions = [
                    "manage_messages",
                    "read_messages",
                    "send_messages",
                    "manage_roles",
                    "attach_files",
                ]
                result = self._permissions_checker(needed_permissions, fetched_channel)
                if not isinstance(result, str):
                    if data["temprole"] or data["autorole"]:
                        await self.data.guild(ctx.guild).active.set(true_or_false)
                        message = "Captcher is now {term}activate.".format(
                            term="" if true_or_false else "de"
                        )
                    else:
                        message = (
                            "Cannot complete request: No temporary or automatic role "
                            "are configured."
                        )
                else:
                    message = result
            else:
                message = "Cannot complete request: No channel are configured."
                if channel_id:
                    await self.data.guild(ctx.guild).verification_channel.clear()
        else:
            await ctx.send_help()
            message = box(
                "Captcher is {term}activated.".format(term="" if data["active"] else "de")
            )
        await ctx.send(message)

    @config.command()
    @commands.bot_has_permissions(administrator=True)
    async def autoconfig(self, ctx: commands.Context):
        """Automatically set Captcher."""
        await ctx.send(
            "This command will:\n"
            "- Create a new role called: Unverified\n"
            "- Create a new channel called: #verification\n"
            "- Create a new channel called: #verification-logs\n"
            "\nBot will overwrite all channels to:\n"
            "- Do not allow Unverified to read in others channels.\n"
            "- Unverified will be able to read & send message in #verification.\n"
            "\nDo you wish to continue?"
        )
        try:
            predicator = MessagePredicate.yes_or_no(ctx)
            await self.bot.wait_for("message", timeout=30, check=predicator)
        except asyncio.TimeoutError:
            await ctx.send("Command cancelled, caused by timeout.")
        if predicator.result:
            if not ctx.channel.permissions_for(ctx.guild.me).administrator:
                await ctx.send("I require the Administrator permission first.")
                return  # In case it's funny to remove perm after using command.
            await self.data.guild(ctx.guild).clear()
            possible_result = await self._overwrite_server(ctx)
            if possible_result:
                await ctx.send(possible_result)
                return
        else:
            await ctx.send("Uhm, why does the captain' had this idea...")
            return
        r = await self._ask_for_role_add(ctx)
        if r:
            await ctx.send("Configuration is done. Activate Captcher? (y/n)")
            try:
                predicator = MessagePredicate.yes_or_no(ctx)
                await self.bot.wait_for("message", timeout=30, check=predicator)
            except asyncio.TimeoutError:
                await ctx.send("Question cancelled, caused by timeout.")
            if predicator.result:
                await self.data.guild(ctx.guild).active.set(True)
            await ctx.send("Done.")

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def challengeuser(
        self, ctx: commands.Context, user: discord.Member, *, reason: str = None
    ):
        """Make an user pass the captcha again."""
        if user.bot:  # Do not challenge bot.
            await ctx.send("Bots are my friend, I cannot let you do that to them.")
            return
        if user is ctx.author:
            await ctx.send("Really... REALLY? ARE YOU TRYING TO CHALLENGE YOURSELF?")
            return
        if user.top_role >= ctx.author.top_role:
            await ctx.send(
                "This user has a role who is higher or equal to your higher role, I "
                "cannot let you do that."
            )
            return

        data = await self.data.guild(ctx.guild).all()
        # Get channel
        verifchannel = data["verifchannel"]
        if not verifchannel:
            await ctx.send("There is no verification channel registered.")
            return
        channel = self.bot.get_channel(verifchannel)
        if not channel:
            await ctx.send("I cannot find the verification channel, please add one again.")
            return

        # Permissions checker (In case someone changed something meanwhile)
        needed_permissions = [
            "manage_messages",
            "read_messages",
            "send_messages",
            "manage_roles",
            "attach_files",
        ]
        checker = self._permissions_checker(needed_permissions, channel)
        if isinstance(checker, str):
            await ctx.send(checker)
            return  # Missing perm(s)

        await ctx.send(
            "This will remove all roles to the users that will get challenged, he will"
            "receive his roles back after passing the captcha or get kicked if fail, "
            "would you like to continue? (Y/N)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        await self.bot.wait_for("message", check=pred)
        if not pred.result:
            await ctx.send("We're sleeping, for now...")
            return

        # Start challenge
        if not reason:
            reason = (
                "Hello [user], a server administrator challenged you for a second time in "
                "this server, please complete the following captcha. If you fail or take "
                "too much time to answer (5 minutes), you will be automatically kicked "
                "from this server.\nNote: The captcha doesn't include space.".replace(
                    "[user]", user.mention
                )
            )
        roles = self._roles_keeper(user)
        await self._roles_remover(user, roles)
        if data["temprole"]:
            role = ctx.guild.get_role(data["temprole"])
            await user.add_roles(role, reason="Temporary role given by captcha.")
        async with ctx.typing():
            captched, bot_message, user_message = await self.challenger(
                user, channel, f"Challenged manually by {ctx.author}", reason
            )

            final = await channel.send(
                "You {term} the captcha.".format(term="completed" if captched else "failed")
            )
            has_been_kicked = False
            if captched:
                await self._add_roles(user, roles)
                await self._report_log(user, "completed", f"Completed captcha.")
            else:
                await self._report_log(user, "kick", "Failed captcha.")
                result = await self._mute_or_unmute_user(channel, user, False)
                if not result:  # Immediate kick
                    await self._kicker(user, "Failed the captcha. (Immediate kick)")
                    has_been_kicked = True
            await asyncio.sleep(5)
            if not captched and not has_been_kicked:
                await self._kicker(user, "Failed the captcha.")
            await bot_message.delete()
            await user_message.delete()
            await final.delete()
            del self.in_challenge[user.id]
