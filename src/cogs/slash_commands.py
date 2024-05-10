import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os

class slash_commands(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client   
    # Cargar las URLs de gifs desde el archivo JSON
    with open(os.path.join("data", "media.json"), "r") as f:
        media_data = json.load(f)
        self.gifs = media_data.get("gifs", {})

  @commands.Cog.listener()
  async def on_ready(self):
    print("Comandos slash cargados correctamente.")
  
  @app_commands.command(name="serverip", description="Obtén la IP del servidor")
  async def serverip(self, interaction: discord.Interaction):
    await interaction.response.send_message("La IP del servidor es **server.boukencraft.com**", ephemeral=True)
  
  @app_commands.command(name="clear", description="Borra mensajes del canal")
  async def clear(self, interaction: discord.Interaction, amount: int):
    
    try:
        if amount <= 0:
          await interaction.response.send_message("Por favor, introduce un número positivo mayor que 0.", ephemeral=True)
          return  # Sale de la función si la cantidad es 0 o negativa

        if amount > 1:
          await interaction.response.send_message(f"Se han borrado {amount} mensajes.", ephemeral=True)

        else:
          await interaction.response.send_message(f"Se ha borrado {amount} mensaje.", ephemeral=True)

        await interaction.channel.purge(limit=amount
                                        )
    except discord.NotFound:
        print("La interacción ya no existe.")
  
  @app_commands.command(name="mute", description="Mutea a un usuario por un tiempo determinado")
  async def mute(self, interaction: discord.Interaction, member: discord.Member, time_minutes: int):
      # Verifica si el usuario que ejecuta el comando tiene permisos necesarios para mutear a otros usuarios
      if not interaction.user.guild_permissions.manage_roles:
          await interaction.response.send_message("No tienes permisos para mutear a otros usuarios.", ephemeral=True)
          return
      
      # Obtiene el rol de mute de la guild
      mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
      timestamp = interaction.created_at.timestamp()
      
      # Verifica si el rol de mute existe, si no, lo crea
      if not mute_role:
          try:
              mute_role = await interaction.guild.get_role(1210341291821371403)
              for channel in interaction.guild.channels:
                  await channel.set_permissions(mute_role, send_messages=False)
          except discord.Forbidden:
              await interaction.response.send_message("No tengo permisos para obtener el rol de mute.", ephemeral=True)
              return
      
      # Mutea al usuario
      await member.add_roles(mute_role)
      await interaction.response.send_message(f"El usuario {member.mention} ha sido muteado por {time_minutes} minutos.", ephemeral=True)
      
      # Envía el log al canal correspondiente
      log_channel = interaction.guild.get_channel(1210343520582508634)  # ID del canal de logs
      if log_channel:
          initial_message = await log_channel.send(f"El usuario {member.mention} ha sido muteado por {interaction.user.mention}. Volverá <t:{int(timestamp + (time_minutes*60))}:R>")
          gif_url = self.gifs.get("muted")
          await log_channel.send(gif_url)
      # Espera el tiempo especificado antes de quitar el mute
      await asyncio.sleep(time_minutes * 60)
      
      # Quita el mute al usuario
      await member.remove_roles(mute_role)
      await initial_message.edit(content=f"{member.mention} fue muteado por {interaction.user.mention}. *Volvió a los {time_minutes} minutos*  :white_check_mark:")

  
async def setup(client: commands.Bot) -> None:
  await client.add_cog(slash_commands(client))

