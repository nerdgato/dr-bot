import discord
from discord.ext import commands
from decouple import config
from typing import Literal
import subprocess
import threading

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.cogslist = ["prefix_commands", "slash_commands", "logs", "welcome", "anti_spam", "normas"]

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
async def reload(interaction: discord.Interaction, cog:Literal["prefix_commands", "slash_commands", "logs", "welcome", "anti_spam", "normas"]):
  try:
    await client.reload_extension(name="cogs."+cog.lower())
    await interaction.response.send_message(f"Se recargó **{cog}.py** exitosamente.", ephemeral=True)
  except Exception as e:
    print(e)
    await interaction.response.send_message(f"Error! no se pudo recargar el módulo. Revisa el error abajo \n```{e}```", ephemeral=True)

def execute_js_script():
    try:
        process = subprocess.Popen(
            ["node", "src/index.js"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        # Esperamos a que el proceso termine y capturamos su salida
        stdout = process.communicate()
        
        if stdout:
            print(f"Ejecución JS terminada correctamente")
        
    except Exception as e:
        print("Error ejecutando el script JS:", e)

# Usamos un hilo para ejecutar el script JS en paralelo
js_thread = threading.Thread(target=execute_js_script)
print("Iniciando el script JS...")
js_thread.start()


client.run(config("TOKEN"))

