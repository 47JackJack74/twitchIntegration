from twitchio.ext import commands

class GeneralCommands(commands.Component):
    
    @commands.command(aliases=["hello", "howdy", "hey"])
    async def hi(self, ctx: commands.Context):
        await ctx.reply(f"Hello {ctx.chatter.mention}!")

    @commands.group(invoke_fallback=True)
    async def socials(self, ctx: commands.Context):
        await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

    @socials.command(name="discord")
    async def socials_discord(self, ctx: commands.Context):
        await ctx.send("discord.gg/...")