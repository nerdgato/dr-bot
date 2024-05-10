from discord.ext import commands

class prefix_commands(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.Cog.listener()
  async def on_ready(self):
    print("Comandos prefix cargados correctamente.")

  @commands.command()
  async def ip(self, ctx):
    await ctx.channel.purge(limit=1)
    await ctx.send("La IP del servidor es **server.boukencraft.com**")
  
  @commands.command()
  async def kek(self, ctx):
    await ctx.channel.purge(limit=1)
    await ctx.send("https://imgur.com/kTavQzB")

async def setup(client) -> None:
  await client.add_cog(prefix_commands(client))

