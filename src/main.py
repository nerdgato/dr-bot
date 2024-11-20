import discord
from discord.ext import commands
from decouple import config
from typing import Literal

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.cogslist = ["prefix_commands", "slash_commands", "logs", "welcome", "anti_spam", "reportes", "normas", "buttons"]

    async def on_ready(self):
        print(f"El bot {self.user.name} se ha conectado correctamente.")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)
    
    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(f"cogs.{ext}")

client = Client()

@client.tree.command(name="reload", description="Recarga una clase Cog")
async def reload(interaction: discord.Interaction, cog:Literal["prefix_commands", "slash_commands", "logs", "welcome", "anti_spam", "reportes", "normas", "buttons"]):
  try:
    await client.reload_extension(name="cogs."+cog.lower())
    await interaction.response.send_message(f"Se recargó **{cog}.py** exitosamente.", ephemeral=True)
  except Exception as e:
    print(e)
    await interaction.response.send_message(f"Error! no se pudo recargar el módulo. Revisa el error abajo \n```{e}```", ephemeral=True)


client.run(config("TOKEN"))