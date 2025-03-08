import os
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from motor import MotorCollection


STATS_WEBHOOK_URL = os.environ.get("U_WEBHOOK_URL")


class Cache(commands.Cog):
    """Caching for modlogs"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.collection: MotorCollection = bot.api.get_plugin_partition(self)

        self.cache_update.start()

    async def cog_unload(self):
        self.cache_update.cancel()

    @tasks.loop(hours=24)
    async def cache_update(self):
        # Guilds
        for guild in self.bot.guilds:
            await self.collection.find_one_and_update(
                {
                    "type": 1, # guild
                    "id": guild.id,
                },
                {"$set": {
                    "name": guild.name,
                    "icon": guild.icon.key,
                    "roles": [ r.id for r in guild.roles ],
                    "channels": [ c.id for c in guild.channels ],
                    "_last_updated": discord.utils.utcnow(),
                },
                "$addToSet": {
                    "bot_ids": self.bot.user.id,
                }},
                upsert=True,
            )

    @cache_update.before_loop
    async def before_cache_update(self):
        await self.bot.wait_until_ready()

    @cache_update.error
    async def cache_update_error(self, exc: Exception):
        await self.wh.send(f"Exception in cache_update: {type(exc).__name__}: {exc} ({self.bot.user.name} `{self.bot.user.id}`)")
        await self.wh.send(f"```{traceback.format_exc()}```")

    @property
    def wh(self) -> discord.Webhook:
        return discord.Webhook.from_url(STATS_WEBHOOK_URL, client=self.bot)

async def setup(bot):
    await bot.add_cog(Cache(bot))
