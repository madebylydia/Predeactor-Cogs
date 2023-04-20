import discord
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus


class TemplateMenu(menus.MenuPages, inherit_buttons=False):
    def __init__(self, sources: dict, timeout: int = 60):
        self.result = None
        super().__init__(sources, timeout=timeout, delete_message_after=True)

    @menus.button(
        "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}", position=menus.First(0)
    )
    async def go_back(self, payload):
        # Logic: https://github.com/fixator10/Fixator10-Cogs/blob/V3.leveler_abc/leveler/menus/backgrounds.py
        # Leveler rewrite, in case the page is deleted and I don't notice (merge)
        if self.current_page == 0:
            await self.show_page(self._source.get_max_pages() - 1)
        else:
            await self.show_checked_page(self.current_page - 1)

    @menus.button("\N{BLACK CIRCLE FOR RECORD}\N{VARIATION SELECTOR-16}", position=menus.First(1))
    async def select(self, payload):
        self.result = await self.source.get_page(self.current_page)
        self.stop()

    @menus.button(
        "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}", position=menus.First(2)
    )
    async def go_next(self, payload):
        # Logic: https://github.com/fixator10/Fixator10-Cogs/blob/V3.leveler_abc/leveler/menus/backgrounds.py
        # Leveler rewrite, in case the page is deleted and I don't notice (merge)
        if self.current_page == self._source.get_max_pages() - 1:
            await self.show_page(0)
        else:
            await self.show_checked_page(self.current_page + 1)

    @menus.button("\N{BLACK SQUARE FOR STOP}\N{VARIATION SELECTOR-16}", position=menus.First(3))
    async def stop_menu(self, payload):
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result


class TemplatePage(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu: TemplateMenu, page):
        embed = discord.Embed(
            title="Choose your template:",
            color=await menu.ctx.embed_color(),
            description=box(page),
        )
        embed.set_footer(
            text="Use \N{BLACK CIRCLE FOR RECORD}\N{VARIATION SELECTOR-16} to select your template."
        )
        return embed
