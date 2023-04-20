# TODO: Add custom exception so we stop do stupid guess

import asyncio
from datetime import datetime
from os import listdir
from os.path import isfile, join
from random import randint
from typing import Literal, Optional

import discord
from discord.utils import get
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import (
    bold,
    error,
    humanize_list,
    info,
    inline,
)
from redbot.core.utils.predicates import MessagePredicate

from captcha.image import ImageCaptcha


class Core(commands.Cog):
    """Functions for Captcher.

    You use them, you die.
    No, seriously, try to keep yourself from touching this.
    """

    __author__ = ["Predeactor"]
    __version__ = "Beta 0.5.1"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        pass

    # Why just a pass? This cog assume that an user was here when code was trigger
    # and the cog will automatically remove anything about the user after some time.
    # (cache). And cache is automatically reset at cog reload/bot restart.

    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=495954055)
        self.data.register_guild(
            autorole=None,
            verifchannel=None,
            active=False,
            logschannel=None,
            temprole=None,
        )
        self.path = bundled_data_path(self)
        self.in_challenge = {}  # Try to improve this part, it sound like pain and killing.
        super(Core, self).__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return (
            "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}\nCog in beta,"
            "unwanted behavior and/or bugs can happens."
        ).format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    def _generate_code_and_image(self):
        """Return the generated code with the generated image.

        Returns:
            str: Code in the captcha.
            BytesIO: The object that contain the image.
        """
        code = str(randint(1000, 999999))  # Cannot start with leading 0...
        file_fonts = [
            f"{self.path}/" + f for f in listdir(self.path) if isfile(join(self.path, f))
        ]
        return (
            code,
            ImageCaptcha(fonts=file_fonts).generate(code),
        )

    async def challenger(
        self,
        member: discord.Member,
        channel: discord.TextChannel,
        start_reason: str,
        start_message: Optional[str] = None,
    ):
        """
        Starting method for challenging an user.
        Before sending any messages, this will check for channel permissions.

        Parameters:
            member: discord.Member, Member to challenge.
            channel: discord.TextChannel, Channel where to send captcha.
            start_reason: str, Reason for starting captcha, will be send in logs if
             possible.
            start_message: Optional[str], Message that will be sent when sending
             captcha, if omitted, default message will be used.

        Returns:
            bool or str: A string will be returned if permission(s) are
             missing (Use isinstance()), else a boolean will be returned to know if
             the captcha was correct or wrong.
            discord.Message: Message the bot sent with the captcha.
            discord.Message: User's message.
        """
        needed_permissions = [
            "manage_messages",
            "read_messages",
            "send_messages",
            "manage_roles",
            "attach_files",
        ]
        checker = self._permissions_checker(needed_permissions, channel)
        if isinstance(checker, str):
            return checker, None, None  # There's missing perm(s)
        if not start_message:
            start_message = (
                "Hello {member}, this server include an extra security layout to protect "
                "their members. You're asked to complete a security captcha in order to "
                "join this server. If you fail or take too much time to answer (5 "
                "minutes), you will be automatically kicked from this server.\nNote: "
                "The captcha doesn't include space.".format(member=member.mention)
            )
        return await self._challenge(member, channel, start_reason, start_message)

    @staticmethod
    def _permissions_checker(permissions: list, channel: discord.TextChannel):
        """Function to checks if the permissions are available.

        Parameters:
            permissions: list - List of permissions needed.
            channel: discord.TextChannel - Channel where permissions will be checked.

        Returns:
            bool or str: If all permissions are given to bot, it will return
             True, else it return a text which include missing permissions.
        """
        missing_perm = [
            permission.replace("_", " ").title()
            for permission in permissions
            if not getattr(channel.permissions_for(channel.guild.me), permission)
        ]

        if missing_perm:
            return (
                "I am missing the following permission{plural} in {channel} "
                "before I start:\n{permissions}"
            ).format(
                plural="s" if len(missing_perm) > 1 else "",
                channel=channel.name,
                permissions="\n- ".join(("", *map(inline, missing_perm))),
            )
        return True

    async def _challenge(self, m: discord.Member, c: discord.TextChannel, sr: str, sm: str):
        """Start challenging an user by sending a captcha.

        Parameters:
            m: discord.Member, Member to challenge.
            c: discord.TextChannel, Channel where to send captcha.
            sr: str, Reason for starting captcha, will be send in logs if possible.
            sm: str, Message that will be sent when sending captcha, optional.

        Returns
            bool: If captcha has been completed, may return None if it was
             impossible to send.
            discord.Message: Message sent by the bot, will be
             automatically deleted after 5 minutes, may return None
            discord.Message: User's message received for captcha, may
             return None if member left.
        """
        code, image = self._generate_code_and_image()
        try:
            bot_message = await c.send(
                content=sm,
                file=discord.File(image, filename=str(m.id) + "-captcha.png"),
                delete_after=300,  # We don't want to let the message here
                tts=True,
            )
        except discord.Forbidden:  # Shouldn't happens
            await self._report_log(
                m,
                "error",
                "Cannot send the captcha message in the verification channel.",
            )
            return None, None, None
        # Creating a cache for the user
        self.in_challenge[m.id] = {}
        self.in_challenge[m.id]["bot_message"] = bot_message
        await self._report_log(m, "started", sr)
        #  Waiting for user input
        success, user_message = await self._predication_result(code, m, c)
        if m.id in self.in_challenge:  # To be sure the user is still in the server
            return success, bot_message, user_message
        return None, bot_message, None  # Leave guild grrr, bad guys!

    async def _predication_result(
        self, code: str, member: discord.Member, channel: discord.TextChannel
    ):
        """Function to wait for user input.

        Parameters:
            code: str, The code that the user should give.
            member: discord.Member, The member we are waiting message for.
            channel: discord.TextChannel, The channel where we are waiting for message.

        Returns:
            bool: If the captcha was correct, wrong or not answered.
            discord.Message: User's message if a message was sent.
        """
        try:
            user_message = await self.bot.wait_for(
                "message",
                timeout=300,
                check=MessagePredicate.same_context(user=member, channel=channel),
            )
        except asyncio.TimeoutError:
            return False, None  # Maybe use None too? Anyway, custom errors so F
        return user_message.content == str(code), user_message

    async def _give_role(self, member: discord.Member):
        """Function to give and/or remove role from member.
        This will automatically grab roles from server's config.

        Parameters:
            member: discord.Member, The member we will act on.

        Returns:
            bool: True if adding/remove role succeeded, else False.
            str: A string to use for logging.
        """
        to_add = await self.data.guild(member.guild).autorole()
        to_remove = await self.data.guild(member.guild).temprole()
        actions = []
        try:
            if to_add:
                to_add = member.guild.get_role(to_add)
                await member.add_roles(to_add, reason="Adding auto role by Captcher.")
                actions.append("added automatically role")
            if to_remove:
                to_remove = member.guild.get_role(to_remove)
                if to_remove in member.roles:
                    await member.remove_roles(
                        to_remove, reason="Removing temporary role by Captcher."
                    )
                    actions.append("removed temporary role")
        except discord.Forbidden:
            return False, "Missing permissions. (Manage Roles)"
        return (
            True,
            humanize_list(actions).capitalize() if actions else "No action taken.",
        )

    async def _report_log(
        self,
        member: discord.Member,
        report_type: Literal["started", "error", "completed", "kick", "other"],
        reason: str,
    ):
        # TODO: Edit the actual message instead of sending a new message.
        """Send a message in the server's log channel for the given member.

        Parameters:
            member: The member where the report come from.
            report_type: The report's type. Must be started, error, completed, kick or other.
            reason: The report reason.

        Return:
            discord.Message: The message sent by the bot in logs or None if impossible
             to send.
        """
        level_list = {
            "started": bold(info(f"{member}: Started a captcha verification: ")) + reason,
            "error": bold(error(f"{member}: Error will Captcha was running: ")) + reason,
            "completed": bold(f"\N{WHITE HEAVY CHECK MARK} {member}: Completed Captcha: ")
            + reason,
            "kick": bold(f"\N{WOMANS BOOTS} {member}: Kicked: ") + reason,
            "other": bold(f"{member}: Other report: ") + reason,
        }
        channel = await self._get_log_channel(member)
        if channel:
            message = level_list[report_type]
            try:
                return await channel.send(message)
            except (discord.HTTPException, discord.Forbidden):
                pass
        return None

    async def _get_log_channel(self, member: discord.Member):
        """Obtain the guild's log channel for the given member.

        Parameters:
            member, discord.Member, The member, so we can find out the guild where to
             send the message.

        Return:
              discord.Channel: The log channel, or None if not set/cannot be
               found.
        """
        if member.id in self.in_challenge and "logschannel" in self.in_challenge[member.id].keys():
            return self.in_challenge[member.id]["logschannel"]
        channel_id = await self.data.guild(member.guild).logschannel()
        if not channel_id:
            return None
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await self.data.guild(member.guild).logschannel.set(None)
            return None
        self.in_challenge[member.id] = {}
        self.in_challenge[member.id]["logschannel"] = channel
        return channel

    async def _kicker(self, member: discord.Member, reason: str):
        """Kick a member, but try to DM him before. Shouldn't be used for other purpose.

        Parameters:
            member: discord.Member, The member we're kicking.
            reason: str, The reason for why we're kicking the user, will be shown in
             modlog and logs channel.

        Return:
            bool: True if succeeded, else return False.
        """
        # TODO: Only alert kick through Captcher logs
        try:
            try:  # DMing user before he got kicked.
                await member.send(
                    f"Hello, you have been kicked from {member.guild} for the following"
                    f" reason: {reason}"
                )
                dmed = "received a message before kicking."
            except discord.HTTPException:
                dmed = "didn't received message before kicking."
            await member.kick()
            await modlog.create_case(
                self.bot,
                member.guild,
                datetime.now(),
                action_type="kick",
                user=member,
                moderator=self.bot.user,
                reason=(
                    "Automatic kick by Captcher. Either not answering or wrong in "
                    f"answering to captcha. User {dmed}"
                ),
            )
            await self._report_log(member, "kick", reason + f"\nUser {dmed}")
            return True
        except discord.HTTPException:
            await self._report_log(
                member,
                "error",
                f"Failed to kick {member}, missing permissions." + f"\nUser {dmed}",
            )
        return False

    @staticmethod
    def _roles_keeper(member: discord.Member):
        """A function to return a list of all role the member actually have.

        Parameter:
            member, discord.Member, The user we want to list roles.
        Return:
             list: A list of discord.Role.
        """
        roles = member.roles[-1:0:-1]
        lister = []
        if roles:
            for role in roles:
                lister.append(role)
        return lister or None

    @staticmethod
    async def _roles_remover(member: discord.Member, roles_to_remove: list):
        """Remove all roles from a member.

        Parameters:
            member: discord.Member, The member we want to remove roles.
            roles_to_remove: list, The list of roles we will remove.

        Return:
            bool: True if succeeded, None if no role was in list or False in case of
             missing permissions.
        """
        if not roles_to_remove:
            return None
        for role in roles_to_remove:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                return False
        return True

    @staticmethod
    async def _add_roles(member: discord.Member, roles_list: list):
        """Add roles to a member from a list.

        Parameters:
            member: discord.Member, The member we want to add roles.
            roles_list, list, The list of roles we will add.

        Return:
            bool: True if succeeded, None if no role was in list or False in case of
             missing permissions.
        """
        if not roles_list:
            return None
        for role in roles_list:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                return False
        return True

    async def _overwrite_server(self, ctx: commands.Context):
        """Function to rewrite whole server. DANGEROUS TO USE.

        Return:
            str: In case there's already a role called 'Unverified'.
        """
        async with ctx.typing():
            trying_getting_role = get(ctx.guild.roles, name="Unverified")
            if trying_getting_role:
                return "A role called 'Unverified' already exist, please delete it first."
            role = await ctx.guild.create_role(
                name="Unverified",
                mentionable=True,
                reason="Automatic creation by Captcher (Automatic setup)",
            )

            verification_overwrite = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    manage_messages=True,
                    send_messages=True,
                    attach_files=True,
                ),
            }

            logs_overwrites = self._make_staff_overwrites(
                await self.bot.get_mod_roles(ctx.guild),
                await self.bot.get_admin_roles(ctx.guild),
                ctx.guild.me,
                ctx.guild.default_role,
            )

            need_channel_change: dict = {}
            for category in ctx.guild.categories:  # Categories overwrites
                actual_perm = category.overwrites
                actual_perm[role] = discord.PermissionOverwrite(read_messages=False)
                await category.edit(overwrites=actual_perm)
                for channel in category.channels:
                    channel_perm = channel.overwrites
                    if role not in channel_perm:  # In case the channel is not synced
                        need_channel_change[channel] = channel_perm
            for channel in need_channel_change.items():  # Overwriting unsynced channels
                actual_perm = channel[1]
                actual_perm[role] = discord.PermissionOverwrite(read_messages=False)
                await channel[0].edit(overwrites=actual_perm)

            verif = await ctx.guild.create_text_channel(
                "verification", overwrites=verification_overwrite
            )
            logs = await ctx.guild.create_text_channel(
                "verification-logs", overwrites=logs_overwrites
            )
            await self.data.guild(ctx.guild).verifchannel.set(verif.id)
            await self.data.guild(ctx.guild).logschannel.set(logs.id)
            await self.data.guild(ctx.guild).temprole.set(role.id)

    @staticmethod
    def _make_staff_overwrites(
        mods: list, admins: list, me: discord.Member, default: discord.Role
    ):
        """Obtain a list of permissions for staff."""
        data = {
            admin: discord.PermissionOverwrite(read_messages=True, send_messages=False)
            for admin in admins
        }

        for mod in mods:
            data[mod] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
        data[default] = discord.PermissionOverwrite(read_messages=False)
        data[me] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        return data

    async def _mute_or_unmute_user(
        self, channel: discord.TextChannel, user: discord.Member, can_send_message: bool
    ):
        """This function mute the user in the given channel.

        Parameters:
            channel: discord.TextChannel, Channel where we act on the user.
            user: discord.Member, The user we're acting on.
            can_send_message: If the user should be able to talk. If False, will mute
             user, else, will remove how overwrite.

        Returns:
            bool: If the action was succeeded.
        """

        actual_perm = channel.overwrites
        if can_send_message:
            if user in actual_perm:
                del actual_perm[user]
            else:
                actual_perm[user] = discord.PermissionOverwrite(send_message=True)
        else:
            actual_perm[user] = discord.PermissionOverwrite(send_messages=False)
        try:
            await channel.edit(reason="Mute for captcher.", overwrites=actual_perm)
            return True
        except discord.Forbidden:
            await self._report_log(
                user,
                "error",
                f"Cannot mute member, missing permissions in {channel.name}",
            )
        return False

    async def _ask_for_role_add(self, ctx: commands.Context):
        await ctx.send("Do you use a role to access to the server? (y/n)")
        try:
            predicator = MessagePredicate.yes_or_no(ctx)
            await self.bot.wait_for("message", timeout=30, check=predicator)
        except asyncio.TimeoutError:
            await ctx.send("Question cancelled, caused by timeout.")
            return
        if predicator.result:
            await ctx.send(
                "Which role should I give when user pass captcha? (Role ID/Name/Mention)"
            )
            role = MessagePredicate.valid_role(ctx)
            try:
                await self.bot.wait_for("message", timeout=60, check=role)
            except asyncio.TimeoutError:
                await ctx.send("Question cancelled, caused by timeout.")
                return
            await self.data.guild(ctx.guild).autorole.set(role.result.id)
        return True

    # Events/Listeners

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Cog's listener to send captcha if parameter are so."""
        if member.bot:
            return  # We ignore bots

        data = await self.data.guild(member.guild).all()
        active = data["active"]
        guild_channel_id = data["verifchannel"]
        temprole = data["temprole"]

        if not active:
            return
        if not guild_channel_id:
            return  # We don't know where the captcha must be sent

        guild_channel = self.bot.get_channel(guild_channel_id)
        if not guild_channel:
            await self._report_log(
                member,
                error,
                "Cannot find the verification channel, deleting data and deactivating Captcher.",
            )
            await self.data.guild(member.guild).verifchannel.clear()
            await self.data.guild(member.guild).active.clear()
            return

        if temprole:
            role = member.guild.get_role(temprole)
            if not role:
                await self.data.guild(member.guild).temprole.clear()  # No more temporary role bye
                await self.data.guild(member.guild).temprole.clear()
                return
            try:
                await member.add_roles(role, reason="Temporary role given by captcha.")
            except discord.Forbidden:
                await self._report_log(
                    member,
                    error,
                    (
                        "I was unable to give the temporary role due to missing permissions, "
                        "aborting and deactivating Captcher."
                    ),
                )
                return

        success, bot_message, user_message = await self.challenger(
            member, guild_channel, "Joined the server."
        )
        if isinstance(success, str):  # We got an error with permissions
            return
        if temprole and role not in member.roles:
            return  # Assuming we gave him manually the role
        if (success and user_message) is None:
            return  # Left in the meantime
        final = await guild_channel.send(
            "You {term} the captcha.".format(term="completed" if success else "failed")
        )
        has_been_kicked = False
        if success:
            gsuccess, log_message = await self._give_role(member)
            if gsuccess:
                await self._report_log(member, "completed", f"Completed captcha: {log_message}")
            else:
                await self._report_log(
                    member,
                    "error",
                    f"Error will trying to give/remove role(s): {log_message}",
                )
        else:
            result = await self._mute_or_unmute_user(guild_channel, member, False)
            if not result:  # Immediate kick
                await self._kicker(member, "Failed the captcha. (Immediate kick)")
                has_been_kicked = True
        await asyncio.sleep(5)
        if not has_been_kicked and not success:
            await self._kicker(member, "Failed the captcha.")
        await bot_message.delete()
        await user_message.delete()
        await final.delete()
        del self.in_challenge[member.id]

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Cog's listener in case the user leave the server before he complete captcha."""
        if member.id not in self.in_challenge:
            return
        left_guild = self.in_challenge[member.id]["bot_message"].guild
        if left_guild != member.guild:  # Not same guild
            return
        bot_message = self.in_challenge[member.id]["bot_message"]
        await bot_message.delete()
        del self.in_challenge[member.id]
