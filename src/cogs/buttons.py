import discord
from discord.ext import commands
import os
import json

class Buttons(commands.Cog):
    def __init__(self, client):
        self.client = client
        
        # Ruta del archivo de sanciones
        self.sanciones_file = os.path.join("data", "sanciones.json")
        
        # Cargar las sanciones desde el archivo JSON
        self.sanciones = self.cargar_sanciones()
    
    def cargar_sanciones(self):
        """Carga las sanciones desde el archivo JSON."""
        if os.path.exists(self.sanciones_file):
            with open(self.sanciones_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            # Si no existe el archivo, devuelve un diccionario vacío
            return {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Botones cargados correctamente.")
        channel_id = 1308814397321384081
        channel = self.client.get_channel(channel_id)
        message = await channel.fetch_message(channel.last_message_id)
        
        # Crear el botón con un custom_id
        button = discord.ui.Button(label="Ver Sanciones", style=discord.ButtonStyle.red, custom_id="ver_sanciones_button")
        view = discord.ui.View()
        view.add_item(button)
        
        # Asociar la acción del botón
        button.callback = self.ver_sanciones  # Aquí se asocia el callback
        
        await message.edit(view=view)

    async def ver_sanciones(self, interaction: discord.Interaction):
        # Asegúrate de que la interacción se pueda manejar en cualquier momento
        if interaction.data["custom_id"] == "ver_sanciones_button":
            user_id = str(interaction.user.id)
            
            # Verificar si el usuario tiene sanciones registradas
            if user_id not in self.sanciones or not self.sanciones[user_id]:
                await interaction.response.send_message(
                    "No tienes sanciones registradas.", ephemeral=True
                )
                return

            embeds = []  # Lista para acumular los embeds

            # Crear un embed separado por cada sanción
            for i, sancion in enumerate(self.sanciones[user_id], 1):
                embed = discord.Embed(
                    title=f"Sanción {i}",
                    description=f"**Motivo:** {sancion['motivo']}\n**Fecha:** {sancion['fecha']}",
                    color=discord.Color.red()
                )
                embeds.append(embed)  # Añadir el embed a la lista

            # Enviar todos los embeds juntos en un solo mensaje
            await interaction.response.send_message(embeds=embeds, ephemeral=True)

async def setup(client):
    await client.add_cog(Buttons(client))
