import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import json
import requests
import os
from cogs.database import inicializar_db, guardar_sancion, cargar_sanciones, actualizar_sancion_con_imagen
from dotenv import load_dotenv

load_dotenv()

# Inicializar la base de datos
inicializar_db()

# Función para subir imágenes a Imgur
def subir_a_imgur_directo(imagen_data, sancion_id):
    client_id = os.getenv("IMGUR_CLIENT_ID")  # Obtener Client ID de Imgur desde .env
    
    headers = {'Authorization': f'Client-ID {client_id}'}
    data = {
        'type': 'file',
        'title': f'Sanción de Discord #{sancion_id}',
        'description': 'Imagen subida automáticamente desde el bot de Discord.'
    }
    url = "https://api.imgur.com/3/image"
    files = {'image': imagen_data}

    response = requests.post(url, headers=headers, data=data, files=files)
    if response.status_code == 200:
        response_data = response.json()
        return response_data['data']['link']
    else:
        print(f"Error al subir la imagen: {response.text}")
        return None


class slash_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        with open(os.path.join("data/media.json"), "r") as f:
            media_data = json.load(f)
            self.gifs = media_data.get("gifs", {})

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f"Comandos slash sincronizados en {len(self.client.guilds)} servidores.")

    @app_commands.command(name="sancionar", description="Sanciona a un jugador con un tipo de sanción específico")
    async def sancionar(self, interaction: discord.Interaction, member: discord.Member, tipo_sancion: str, imagen: discord.Attachment):
        tipos_permitidos = ["spam", "toxicidad", "flood", "off-topic"]
        if tipo_sancion.lower() not in tipos_permitidos:
            await interaction.response.send_message(
                "Tipo de sanción no válido. Los tipos permitidos son: spam, toxicidad, flood, off-topic.", ephemeral=True
            )
            return
        
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "No tienes permisos para sancionar a otros usuarios.", ephemeral=True
            )
            return

        if imagen is None:
            await interaction.response.send_message(
                "Es obligatorio proporcionar una imagen para la sanción.", ephemeral=True
            )
            return

        # Registrar sanción en la base de datos
        fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M")
        sancion_id = guardar_sancion(str(member.id), tipo_sancion, fecha_actual, None)

        # Subir imagen a Imgur
        imagen_data = await imagen.read()
        url_imagen = subir_a_imgur_directo(imagen_data, sancion_id)

        # Actualizar la sanción con la URL de la imagen
        actualizar_sancion_con_imagen(sancion_id, url_imagen)

        # Añadir rol de sanción
        rol_sancion = discord.utils.get(interaction.guild.roles, name="Sanctioned")
        if not rol_sancion:
            await interaction.response.send_message("El rol 'Sancionado' no existe en el servidor.", ephemeral=True)
            return

        await member.add_roles(rol_sancion)
        
        await interaction.response.send_message(
            f"{member.mention} ha sido sancionado por {tipo_sancion}. Imagen: {url_imagen}", ephemeral=True
        )

    # Autocompletado para el parámetro 'tipo_sancion'
    @sancionar.autocomplete("tipo_sancion")
    async def sancionar_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,  # Lo que el usuario ha escrito hasta ahora
    ) -> list[app_commands.Choice[str]]:
        # Filtrar las opciones según lo que el usuario ha escrito
        tipos_permitidos = ["spam", "toxicidad", "flood", "off-topic"]
        opciones = [tipo for tipo in tipos_permitidos if current.lower() in tipo.lower()]
        # Devolver una lista de opciones como `app_commands.Choice`
        return [app_commands.Choice(name=tipo, value=tipo) for tipo in opciones]

    @app_commands.command(name="ver_sanciones", description="Muestra las sanciones de un jugador")
    async def ver_sanciones(self, interaction: discord.Interaction, member: discord.Member):
        sanciones = cargar_sanciones(str(member.id))
        if not sanciones:
            await interaction.response.send_message(
                f"{member.mention} no tiene sanciones registradas.", ephemeral=True
            )
            return

async def setup(client: commands.Bot):
    await client.add_cog(slash_commands(client))
