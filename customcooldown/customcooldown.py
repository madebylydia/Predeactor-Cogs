import asyncio
from contextlib import suppress as suppressor
from datetime import datetime
from string import Template
from typing import Literal

import discord
from redbot.core import Config, checks, commands
from redbot.core.commands.converter import parse_timedelta
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import (
    bold,
    box,
    humanize_list,
    humanize_timedelta,
    pagify,
    warning,
)
from redbot.core.utils.predicates import MessagePredicate

default_channel_message = (
    "Sorry $member, this channel is ratelimited! You'll be able to post again in $channel in "
    "time."
)
default_category_message = (
    "Sorry $member, this category is ratelimited! You'll be able to post again in $channel in "
    "$time."
)


class CustomCooldown(commands.Cog):
    """Create a customizable cooldown to each channels and category.

    This cooldown is moderated by the bot itself.
    """

    __author__ = ["Maaz", "Predeactor"]
    __version__ = "v1.4.01"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        if requester in ("owner", "user_strict", "discord_deleted_user"):
            for guild in self.bot.guilds:
                await self.config.member_from_ids(guild.id, user_id).clear()

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=231120028796)
        self.config.register_member(ignored=False)
        self.config.register_role(ignored=False)
        self.config.register_guild(
            cooldown_channels={},
            cooldown_categories={},
            send_dm=False,
            ignore_bot=True,
            channel_message=default_channel_message,
            category_message=default_category_message,
        )
        self.config.register_global(version=None)
        self.dmed = []
        super(CustomCooldown, self).__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    # Handling Functions

    async def _handle_channel_cooldown(self, message, cooldown_channel, send_dm):
        now = round(datetime.timestamp(datetime.now()))
        channel = message.channel
        user = message.author
        channel_data = cooldown_channel.get(str(channel.id), None)

        if not channel_data:
            return

        # If user is not registered, add him and stop.
        if str(user.id) not in channel_data["users_on_cooldown"]:
            channel_data["users_on_cooldown"][str(message.author.id)] = now
            cooldown_channel[str(message.channel.id)] = channel_data
            await self.config.guild(message.guild).cooldown_channels.set(cooldown_channel)
        else:
            last_message_date = channel_data["users_on_cooldown"][str(message.author.id)]
            total_seconds = now - last_message_date
            if total_seconds <= channel_data["cooldown_time"]:
                try:
                    await message.delete()
                    deleted = True
                except (discord.NotFound, discord.Forbidden):
                    deleted = False
                if send_dm and not user.bot:
                    with suppressor(Exception):
                        remaining_time = humanize_timedelta(
                            seconds=(channel_data["cooldown_time"] - total_seconds)
                        )
                        message_string = Template(
                            await self.config.guild(message.guild).channel_message()
                        )
                        send_me = self._prepare_message(
                            message_string,
                            remaining_time,
                            user.name,
                            channel.name,
                        )
                        await user.send(send_me)
            else:
                deleted = None
                channel_data["users_on_cooldown"][str(message.author.id)] = now
                cooldown_channel[str(message.channel.id)] = channel_data
                await self.config.guild(message.guild).cooldown_channels.set(cooldown_channel)
            # If message deletion wasn't possible:
            if deleted is False:
                await self._dm_owner(message.guild.owner, channel)

    async def _handle_category_cooldown(self, message, cooldown_category, send_dm):
        now = round(datetime.timestamp(datetime.now()))
        channel = message.channel
        user = message.author
        category_data = cooldown_category.get(str(channel.category.id), None)

        if not category_data:
            return
        category = channel.category
        if str(user.id) not in category_data["users_on_cooldown"]:
            category_data["users_on_cooldown"][str(user.id)] = now
            cooldown_category[str(category.id)] = category_data
            await self.config.guild(message.guild).cooldown_categories.set(cooldown_category)
        else:
            last_message_date = category_data["users_on_cooldown"][str(user.id)]
            total_seconds = now - last_message_date
            if total_seconds <= category_data["cooldown_time"]:
                try:
                    await message.delete()
                    deleted = True
                except discord.Forbidden:
                    deleted = False
                if send_dm and not user.bot:
                    with suppressor(Exception):
                        remaining_time = humanize_timedelta(
                            seconds=category_data["cooldown_time"] - total_seconds
                        )
                        message_string = Template(
                            await self.config.guild(message.guild).category_message()
                        )
                        send_me = self._prepare_message(
                            message_string,
                            remaining_time,
                            user.name,
                            channel.category.name,
                        )
                        await user.send(send_me)
            else:
                deleted = None
                category_data["users_on_cooldown"][str(user.id)] = now
                cooldown_category[str(channel.id)] = category_data
                await self.config.guild(message.guild).cooldown_categories.set(cooldown_category)
            # If message deletion wasn't possible:
            if deleted is False:
                await self._dm_owner(message.guild.owner, channel)

    # Slow commannds (For adding/removing/listing cooldowned channels/category)

    @commands.group()
    @commands.guild_only()
    @checks.admin()
    async def slow(self, ctx: commands.GuildContext):
        """Configure categories and channel cooldown."""
        pass

    # Slow: Category

    @slow.group(name="category")
    async def slowcategory(self, ctx: commands.Context):
        """Set categories to cooldown."""
        pass

    @slowcategory.command(name="list")
    async def listcategory(self, ctx: commands.Context):
        """List cooldowned categories."""
        text = ""
        cooldown_categories = await self.config.guild(ctx.guild).cooldown_categories()
        for category_id in cooldown_categories.keys():
            category = self.bot.get_channel(int(category_id))
            if category:
                seconds = cooldown_categories[category_id]["cooldown_time"]
                time = humanize_timedelta(seconds=seconds)
                text += "- {name} (`{id}`) Time: {time}.\n".format(
                    name=category.name, id=category.id, time=time
                )
            else:
                text += "- Category not found: {id}\n".format(id=category_id)
        if text:
            for line in pagify(text):
                await ctx.maybe_send_embed(line)
        else:
            await ctx.send("There's no category to show.")

    @slowcategory.command(name="add")
    async def addcategory(
        self, ctx: commands.Context, category: discord.CategoryChannel, *, time: str
    ):
        """Add a category cooldown.

        Time format can be the following:
        - `1 hour`
        - `1h`
        - `1 hour 5 minutes`
        - `2h30m10s`
        """
        if not category.permissions_for(ctx.me).manage_messages:
            await ctx.send(
                "I require the 'Manage messages' permission to let you use this command."
            )
        cooldown_categories = await self.config.guild(ctx.guild).cooldown_categories()
        if str(category.id) in cooldown_categories:
            await ctx.send(
                "This category is already added to the cooldown. If you want to edit"
                " the cooldown time, use `{prefix}slow channel edit`.".format(
                    prefix=ctx.clean_prefix
                )
            )
            return
        time = self._return_time(time)
        if time:
            await self._update_category_data(ctx, category, time)
            await ctx.send(
                "Done! Every {category}'s channels are now set at 1 message every "
                "{time} seconds. Channels from this category are moderated but new channel "
                "won't be moderated. If you add channels that you want to also add cooldown"
                ", use `{prefix}slow category update`".format(
                    category=category.name, time=time, prefix=ctx.clean_prefix
                )
            )
        else:
            await ctx.send("Your time is not correct to me.")

    @slowcategory.command(name="edit")
    async def editcategory(
        self, ctx: commands.Context, category: discord.CategoryChannel, *, time: str
    ):
        """Edit a category cooldown.

        Time format can be the following:
        - `1 hour`
        - `1h`
        - `1 hour 5 minutes`
        - `2h30m10s`
        """
        cooldown_categories = await self.config.guild(ctx.guild).cooldown_categories()
        if str(category.id) not in cooldown_categories:
            await ctx.send("{category} does not have cooldown.".format(category=category.name))
            return
        time = self._return_time(time)
        if time:
            await self._update_category_data(ctx, category, time)
            await ctx.send(
                "{category} is now set at 1 message every {time} seconds.".format(
                    category=category.name, time=time
                )
            )
        else:
            await ctx.send("Your time is not correct to me.")

    @slowcategory.command(name="delete", aliases=["remove", "del"])
    async def deletecategory(self, ctx: commands.Context, *, category: discord.CategoryChannel):
        """Delete a category cooldown."""
        predicate = MessagePredicate.yes_or_no(ctx)
        await ctx.send(
            warning(
                bold(
                    "Are you sure you want to delete {category} data?".format(
                        category=category.name
                    )
                )
                + " (Y/N)"
            )
        )
        try:
            await self.bot.wait_for("message", check=predicate)
        except asyncio.TimeoutError:
            await ctx.tick()
            return
        if predicate.result:
            await self._delete_category(ctx, category)
            await ctx.tick()
        else:
            await ctx.send("Cooldowned, forever...")

    @slowcategory.command(name="update")
    async def updatecategory(self, ctx: commands.Context, *, category: discord.CategoryChannel):
        """Update category's data to sync with new and old channel(s) into the category."""
        data = await self.config.guild(ctx.guild).cooldown_categories()
        if str(category.id) not in data:
            await ctx.send(
                "This category is not registered into cooldowned categories.\n"
                "Use `{prefix}slow category add` first.".format(prefix=ctx.clean_prefix)
            )
            return
        time = data[str(category.id)]["cooldown_time"]
        await self._update_category_data(ctx, category, time)
        await ctx.tick()

    # Slow: Channel

    @slow.group(name="channel")
    async def slowchannel(self, ctx: commands.GuildContext):
        """Set channels to cooldown."""
        pass

    @slowchannel.command(name="list")
    async def listchannel(self, ctx: commands.Context):
        """List cooldowned channels."""
        text = ""
        cooldown_channels = await self.config.guild(ctx.guild).cooldown_channels()
        for channel_id in cooldown_channels.keys():
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                seconds = cooldown_channels[channel_id]["cooldown_time"]
                time = humanize_timedelta(seconds=seconds)
                text += "- {name} (`{id}`) Time: {time}.\n".format(
                    name=channel.name, id=channel.id, time=time
                )
            else:
                text += "- Channel not found: {id}\n".format(id=channel_id)
        if text:
            for line in pagify(text):
                await ctx.maybe_send_embed(line)
        else:
            await ctx.send("There's no channel to show.")

    @slowchannel.command(name="add")
    async def addchannel(self, ctx: commands.Context, channel: discord.TextChannel, *, time: str):
        """Add a channel cooldown.

        Time format can be the following:
        - `1 hour`
        - `1h`
        - `1 hour 5 minutes`
        - `2h30m10s`
        """
        if not channel.permissions_for(ctx.me).manage_messages:
            await ctx.send(
                "I require the 'Manage messages' permission to let you use this command."
            )
            return
        if str(channel.id) in await self.config.guild(ctx.guild).cooldown_channels():
            await ctx.send(
                "This channel is already added to the cooldown. If you want to edit"
                " the cooldown time, use `{prefix}slow channel edit`.".format(
                    prefix=ctx.clean_prefix
                )
            )
            return
        time = self._return_time(time)
        if not time:
            await ctx.send("Your time is not correct to me.")
            return
        await self._update_channel_data(ctx, channel, time)
        await ctx.send(
            "{channel} is now set at 1 message every {time} seconds.".format(
                channel=channel.mention, time=time
            )
        )

    @slowchannel.command(name="edit")
    async def editchannel(self, ctx: commands.Context, channel: discord.TextChannel, *, time: str):
        """Edit a channel cooldown.

        Time format can be the following:
        - `1 hour`
        - `1h`
        - `1 hour 5 minutes`
        - `2h30m10s`
        """
        if str(channel.id) in await self.config.guild(ctx.guild).cooldown_channels():
            time = self._return_time(time)
        else:
            await ctx.send("{channel} does not have cooldown.".format(channel=channel.mention))
            return
        if not time:
            await ctx.send("Your time is not correct to me.")
        await self._update_channel_data(ctx, channel, time)
        await ctx.send(
            "{channel} is now set at 1 message every {time} seconds.".format(
                channel=channel.mention, time=time
            )
        )

    @slowchannel.command(name="delete", aliases=["remove", "del"])
    async def deletechannel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """Delete a channel cooldown."""
        predicate = MessagePredicate.yes_or_no(ctx)
        await ctx.send(
            warning(
                bold(
                    "Are you sure you want to delete {channel} data?".format(channel=channel.name)
                )
                + " (Y/N)"
            )
        )
        try:
            await self.bot.wait_for("message", check=predicate)
        except asyncio.TimeoutError:
            await ctx.tick()
            return
        if predicate.result:
            await self._delete_channel(ctx, channel)
            await ctx.tick()
        else:
            await ctx.send("Peace and quiet...")

    # Slowset, for settings various settings

    @commands.group()
    @commands.guild_only()
    @checks.admin()
    async def slowset(self, ctx: commands.GuildContext):
        """Set differents options for cooldown."""
        pass

    @slowset.command()
    async def dm(self, ctx: commands.Context, option: bool = None):
        """
        Enable/Disable DM message when triggering cooldown.

        You must use `True` or `False`.
        """
        if option is not None:
            await self.config.guild(ctx.guild).send_dm.set(option)
            if option:
                await ctx.send("I will now DM users when they trigger the cooldown.")
            else:
                await ctx.send("I won't send DM to users anymore.")
        else:
            await ctx.send_help()

    @slowset.command()
    async def ignorebot(self, ctx: commands.Context, option: bool = None):
        """
        Enable/Disable ignoring bots when they send a message in channel
         or category that own a cooldown.

        You must use `True` or `False`.
        """
        if option is not None:
            await self.config.guild(ctx.guild).ignore_bot.set(option)
            if option:
                await ctx.send(
                    "I will now ignore bot when they send a message in "
                    "cooldowned channels/category."
                )
            else:
                await ctx.send("I won't ignore bots anymore.")
        else:
            await ctx.send_help()

    # Slowset: Ignore Users

    @slowset.group(name="ignoreusers", aliases=["ignoreuser", "iu"])
    async def slowignoreusers(self, ctx: commands.GuildContext):
        """Add or remove users from the ignored list of cooldown."""
        pass

    @slowignoreusers.command(name="list")
    async def listignoredusers(self, ctx: commands.Context):
        """List ignored users."""
        text = ""
        ignored_users = await self.config.all_members(ctx.guild)
        if ignored_users:
            for user_id in ignored_users:
                if ignored_users[user_id]["ignored"]:
                    user = await self._get_user(user_id)
                    if user:
                        text += "- {name} (`{id}`).\n".format(name=user.name, id=user.id)
                    else:
                        text += "- User not found: {id}".format(id=user_id)
        if text:
            for line in pagify(text):
                await ctx.maybe_send_embed(line)
        else:
            await ctx.send("No users is ignored.")

    @slowignoreusers.command(name="add")
    async def addignoreusers(self, ctx: commands.Context, *users: discord.Member):
        """Add one or multiples users to the ignored list."""
        if not users:
            await ctx.send_help()
            return
        must_be_added = []
        already_added = []
        is_bot = []
        final_message = ""
        all_members = await self.config.all_members(ctx.guild)

        for user in users:
            if user.bot:
                is_bot.append(user.name)
                continue
            if user.id not in all_members or not all_members[user.id]["ignored"]:
                must_be_added.append(user)
            else:
                already_added.append(str(user))

        for user in must_be_added:
            await self.config.member(user).ignored.set(True)

        if len(is_bot) > 1:
            final_message += "Those members are bots and cannot be added: {bots}\n".format(
                bots=humanize_list(is_bot)
            )
        elif len(is_bot) == 1:
            final_message += "{bot} is a bot and cannot be added.\n".format(bot=is_bot[0])
        if len(already_added) > 1:
            final_message += "Those members are already ignored: {list}".format(
                list=humanize_list(already_added)
            )
        elif len(already_added) == 1:
            final_message += "{user} is already ignored.".format(user=already_added[0])

        if final_message:
            for line in pagify(final_message):
                await ctx.send(line)
        await ctx.tick()

    @slowignoreusers.command(name="delete", aliases=["remove", "del"])
    async def removeignoreusers(self, ctx: commands.Context, *users: discord.Member):
        """Remove one or multiples users on the ignored list."""
        if not users:
            await ctx.send_help()
            return
        must_remove = []
        already_removed = []
        final_message = ""
        all_members = await self.config.all_members(ctx.guild)

        for user in users:
            if user.id in all_members:
                if all_members[user.id]["ignored"]:
                    must_remove.append(user)
                else:
                    already_removed.append(user.name)

        for user in must_remove:
            await self.config.member(user).clear()

        if len(already_removed) > 1:
            final_message = "Those users are already not ignored: {list}".format(
                list=humanize_list(already_removed)
            )
        elif len(already_removed) == 1:
            final_message = "{user} is already not ignored.".format(user=already_removed[0])
        if final_message:
            for line in pagify(final_message):
                await ctx.send(line)
        await ctx.tick()

    # Slowset: Ignore Roles

    @slowset.group(name="ignoreroles", aliases=["ignorerole", "ir"])
    async def slowignoreroles(self, ctx: commands.GuildContext):
        """Add or remove roles from the ignored list of cooldown."""
        pass

    @slowignoreroles.command(name="list")
    async def listignoredroles(self, ctx: commands.Context):
        """List ignored roles."""
        text = ""
        all_roles = await self.config.all_roles()
        guild_roles_id = [role.id for role in ctx.guild.roles]
        in_relation_roles = list(
            set(all_roles).intersection(guild_roles_id)
        )  # This was, we only get guild's roles

        for role_id in in_relation_roles:
            if all_roles[role_id]["ignored"]:
                role = ctx.guild.get_role(role_id)
                if role:
                    text += "- {name} (`{id}`).\n".format(name=role.name, id=role.id)
                else:
                    text += "- Role not found: {id}".format(id=role_id)
        if text:
            for line in pagify(text):
                await ctx.maybe_send_embed(line)
        else:
            await ctx.send("There is no role to ignore.")

    @slowignoreroles.command(name="add")
    async def addignoreroles(self, ctx: commands.Context, *roles: discord.Role):
        """Add one or multiples role to the ignored list."""
        if not roles:
            await ctx.send_help()
            return
        must_be_added = []
        already_added = []
        final_message = ""
        all_roles = await self.config.all_roles()

        for role in roles:
            if role.id in all_roles:
                if not all_roles[role.id]["ignored"]:
                    must_be_added.append(role)
                else:
                    already_added.append(role.name)
            else:
                must_be_added.append(role)

        for role in must_be_added:
            await self.config.role(role).ignored.set(True)

        if len(already_added) > 1:
            final_message += "Those roles are already ignored: {list}".format(
                list=humanize_list(already_added)
            )
        elif len(already_added) == 1:
            final_message += "{role} is already ignored.".format(role=already_added[0])
        if final_message:
            for line in pagify(final_message):
                await ctx.send(line)
        await ctx.tick()

    @slowignoreroles.command(name="delete", aliases=["remove", "del"])
    async def removeignoreroles(self, ctx: commands.Context, *roles: discord.Role):
        """Remove one or multiples roles on the ignored list."""
        if not roles:
            await ctx.send_help()
            return
        already_removed = []
        must_be_removed = []
        message = ""
        all_roles = await self.config.all_roles()

        for role in roles:
            if role.id in all_roles:
                if all_roles[role.id]["ignored"]:
                    must_be_removed.append(role)
                else:
                    already_removed.append(role.name)
            else:
                already_removed.append(role.name)

        for role in must_be_removed:
            await self.config.role(role).ignored.clear()

        if len(already_removed) > 1:
            message = "Those roles are already not ignored: {list}".format(
                list=humanize_list(already_removed)
            )
        elif len(already_removed) == 1:
            message = "{role} is already not ignored.".format(role=already_removed[0])
        if message:
            for line in pagify(message):
                await ctx.send(line)
        await ctx.tick()

    # Slowed : Message settings

    @slowset.command()
    async def channelmessage(self, ctx: commands.Context, *, message: str = None):
        """Change the message to send to user when triggering channels cooldown.

        Parameters:
        - `$time` will be replaced with remaining cooldown time.
        - `$member` will get replaced with member's name.
        - `$channel` will get replaced with channel's name.

        To use default message, use `None` for parameter message.
        """
        if not message:
            await ctx.send_help()
            result = "Actual message:\n" + box(
                await self.config.guild(ctx.guild).category_message()
            )
        if message:
            if message.lower() == "none":
                await self.config.guild(ctx.guild).channel_message.clear()
                result = "Channel message set to default."
            else:
                await self.config.guild(ctx.guild).channel_message.set(message)
                result = "The message has been replaced."
        await ctx.send(result)

    @slowset.command()
    async def categorymessage(self, ctx: commands.Context, *, message: str = None):
        """Change the message to send to user when triggering categories cooldown.

        Parameters:
        - `$time` will be replaced with remaining cooldown time.
        - `$member` will get replaced with member's name.
        - `$channel` will get replaced with category's name.

        To use default message, use `None` for parameter message.
        """
        if not message:
            await ctx.send_help()
            result = "Actual message:\n" + box(
                await self.config.guild(ctx.guild).category_message()
            )
        if message:
            if message.lower() == "none":
                await self.config.guild(ctx.guild).category_message.clear()
                result = "Category message set to default."
            else:
                await self.config.guild(ctx.guild).category_message.set(message)
                result = "The message has been replaced."
        await ctx.send(result)

    # Bypassing

    @commands.group()
    @checks.mod()
    async def bypass(self, ctx):
        """Bypass a user cooldown."""
        pass

    @bypass.command(name="channel")
    async def bypass_channel(self, ctx, member: discord.Member, channel: discord.TextChannel):
        """Resets the cooldown for a user in a channel."""
        cooldown_channels = await self.config.guild(ctx.guild).cooldown_channels()
        if str(channel.id) not in cooldown_channels:
            await ctx.send("{channel} is not on cooldown.".format(channel=channel.mention))
            return
        if str(member.id) not in cooldown_channels[str(channel.id)]["users_on_cooldown"]:
            await ctx.send(
                "{user} is not on cooldown in {channel}.".format(
                    user=member, channel=channel.mention
                )
            )
            return
        del cooldown_channels[str(channel.id)]["users_on_cooldown"][str(member.id)]
        await self.config.guild(ctx.guild).cooldown_channels.set(cooldown_channels)
        await ctx.send(f"{member}'s cooldown in {channel.mention} has been reset.")

    @bypass.command(name="category")
    async def bypass_category(
        self, ctx, member: discord.Member, category: discord.CategoryChannel
    ):
        """Resets the cooldown for a user in a category."""
        cooldown_categories = await self.config.guild(ctx.guild).cooldown_categories()
        if str(category.id) not in cooldown_categories:
            await ctx.send(
                "{category} category is not on cooldown.".format(category=category.name)
            )
            return
        if str(member.id) not in cooldown_categories[str(category.id)]["users_on_cooldown"]:
            await ctx.send(
                "{user} is not on cooldown in {category}.".format(
                    user=member, category=category.name
                )
            )
            return
        del cooldown_categories[str(category.id)]["users_on_cooldown"][str(member.id)]
        await self.config.guild(ctx.guild).cooldown_categories.set(cooldown_categories)
        await ctx.send(
            "{member}'s cooldown in {category} has been reset.".format(
                member=member.name, category=category.name
            )
        )

    # Listener

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        data = await self.config.guild(message.guild).all()

        if data["ignore_bot"] and message.author.bot:
            return
        ignored_roles = await self.config.all_roles()
        for roleid in set([role.id for role in message.author.roles]):
            if roleid in ignored_roles:
                if ignored_roles[roleid].get("ignored", False):
                    return
        members = await self.config.all_members(message.guild)
        if message.author.id in members:
            if members[message.author.id].get("ignored", False):
                return

        cooldown_categories = data["cooldown_categories"]
        cooldown_channels = data["cooldown_channels"]

        categories_ids = []  # Where we store categories ID for a moment.
        categories_channels = []  # Where we store channels we're gonna check.
        for category_id in cooldown_categories:
            categories_ids.append(str(category_id))
        for category_id in categories_ids:
            for channels in cooldown_categories[category_id]["channels"]:
                categories_channels.append(str(channels))
        channel = message.channel
        if str(channel.id) not in list(cooldown_channels.keys()) + categories_channels:
            return

        send_dm = data["send_dm"]
        if str(channel.id) in cooldown_channels:
            await self._handle_channel_cooldown(message, cooldown_channels, send_dm)
        if channel.category and (str(channel.id) in categories_channels):
            await self._handle_category_cooldown(message, cooldown_categories, send_dm)

    # Functions

    async def _update_channel_data(
        self, ctx: commands.Context, channel: discord.TextChannel, time
    ) -> None:
        if isinstance(time, float):
            time = int(time)
        async with self.config.guild(ctx.guild).cooldown_channels() as cooldown_channels:
            cooldown_channels[str(channel.id)] = {
                "cooldown_time": time,
                "users_on_cooldown": {},
            }

    async def _update_category_data(
        self, ctx: commands.Context, category: discord.CategoryChannel, time
    ) -> None:
        if isinstance(time, float):
            time = int(time)
        async with self.config.guild(ctx.guild).cooldown_categories() as cooldown_categories:
            cooldown_categories[str(category.id)] = {
                "cooldown_time": time,
                "users_on_cooldown": {},
                "channels": [channel.id for channel in category.channels],
            }

    async def _delete_channel(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        async with self.config.guild(ctx.guild).cooldown_channels() as cooldown_channels:
            if str(channel.id) in cooldown_channels:
                del cooldown_channels[str(channel.id)]
            else:
                await ctx.send(
                    "I can't find {channel} into the configured cooldown.".format(
                        channel=channel.mention
                    )
                )

    async def _delete_category(
        self, ctx: commands.Context, category: discord.CategoryChannel
    ) -> None:
        async with self.config.guild(ctx.guild).cooldown_categories() as cooldown_categories:
            if str(category.id) in cooldown_categories:
                del cooldown_categories[str(category.id)]
            else:
                await ctx.send(
                    "I can't find {category} into the configured cooldown.".format(
                        category=category.name
                    )
                )

    @staticmethod
    def _return_time(time):
        cooldown_time = parse_timedelta(time)
        if cooldown_time is None:
            return None
        return int(cooldown_time.total_seconds())

    async def _get_user(self, user_id: int):
        user = self.bot.get_user(user_id)
        if user is None:  # User not found
            try:
                user = await self.bot.fetch_user(user_id)
            except (discord.NotFound, discord.HTTPException):
                return None
        return user

    async def _dm_owner(self, owner: discord.Member, channel: discord.TextChannel) -> None:
        if owner.id in self.dmed:
            return
        with suppressor(Exception):
            await owner.send(
                "Hello. I tried to delete a message in {channel} because this "
                "channel is registered as cooldowned, but I was unable to delete "
                "the last message. I need the Manage messages permissions to "
                "delete messages in this channel.\nThis message won't reappear "
                "until the next bot reboot or cog reload.".format(channel=channel.mention)
            )
        self.dmed.append(owner.id)

    @staticmethod
    def _prepare_message(string: Template, time: str, member: str, channel: str) -> str:
        template = {"time": time, "member": member, "channel": channel}
        return string.safe_substitute(template)

    async def _maybe_update_config(self) -> str:
        """Update Config for the new version of CustomCooldown."""
        if not await self.config.version():
            guild_dict = await self.config.all_guilds()
            async for guild_id, info in AsyncIter(guild_dict.items()):
                old_temporary_ignore_roles = info.get("ignore_roles", None)
                if old_temporary_ignore_roles:
                    for role_id in old_temporary_ignore_roles:
                        await self.config.role_from_id(role_id).ignored.set(True)
                    await self.config.guild_from_id(guild_id).ignore_roles.clear()
                old_temporary_ignore_users = info.get("ignore_users", None)
                if old_temporary_ignore_users:
                    for user_id in old_temporary_ignore_users:
                        await self.config.member_from_ids(guild_id, user_id).ignored.set(True)
                    await self.config.guild_from_id(guild_id).ignore_users.clear()
                old_category_message = info.get("category_message", None)
                if old_category_message:
                    new_category_message = (
                        old_category_message.replace("{time}", "$time")
                        .replace("{member}", "$member")
                        .replace("{channel}", "$channel")
                    )
                    await self.config.guild_from_id(guild_id).category_message.set(
                        new_category_message
                    )
                old_channel_message = info.get("category_message", None)
                if old_channel_message:
                    new_channel_message = (
                        old_channel_message.replace("{time}", "$time")
                        .replace("{member}", "$member")
                        .replace("{channel}", "$channel")
                    )
                    await self.config.guild_from_id(guild_id).channel_message.set(
                        new_channel_message
                    )
            await self.config.version.set("1.0.0")
        return "uwu"
