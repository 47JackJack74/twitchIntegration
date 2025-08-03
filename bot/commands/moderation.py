from twitchio.ext import commands

class ModerationCommands(commands.Component):

    @commands.command(aliases=["repeat"])
    @commands.is_moderator()
    async def say(self, ctx: commands.Context, *, content: str):
        await ctx.send(content)