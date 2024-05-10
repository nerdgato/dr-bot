import discord
from discord.ext import commands
from . import prefix_commands

class Logs(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.Cog.listener()
  async def on_ready(self):
    print("Logs cargados correctamente.")
  
  @commands.Cog.listener()
  async def on_message(self, message):
    log_channel = self.client.get_channel(1209856052288426074)

    if message.content.startswith('!'):
      command_name = message.content.split()[0][1:]  # Extraer el nombre del comando sin el prefijo '!'

      if hasattr(prefix_commands.prefix_commands, command_name):
        event_embed = discord.Embed(title="Comando enviado", description="Contenido y origen del comando", color=discord.Color.purple())
        event_embed.add_field(name="Autor del comando:", value=message.author.mention, inline=False)
        event_embed.add_field(name="Canal de origen:", value=message.channel.mention, inline=False)
        event_embed.add_field(name="Contenido del comando:", value=message.content, inline=False)

        await log_channel.send(embed=event_embed)
        
  @commands.Cog.listener()
  async def on_interaction(self, interaction):
      log_channel = self.client.get_channel(1209856052288426074)

      if interaction.type == discord.InteractionType.application_command:
          event_embed = discord.Embed(title="Comando enviado", description="Contenido y origen del comando", color=discord.Color.blue())
          event_embed.add_field(name="Autor del comando:", value=interaction.user.mention, inline=False)
          event_embed.add_field(name="Canal de origen:", value=interaction.channel.mention, inline=False)
          event_embed.add_field(name="Contenido del comando:", value=interaction.data['name'], inline=False)

          await log_channel.send(embed=event_embed)

async def setup(client):
  await client.add_cog(Logs(client))