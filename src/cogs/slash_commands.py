import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import json
import requests
import os
from cogs.database import inicializar_db, guardar_sancion, cargar_sanciones, actualizar_sancion_con_imagen, conectar_db
from dotenv import load_dotenv
import asyncio

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

    @app_commands.command(name="clear", description="Borra un número específico de mensajes en el canal actual")
    async def clear(self, interaction: discord.Interaction, cantidad: int):
        if cantidad <= 0:
            await interaction.response.send_message(
                "Por favor, proporciona un número entero positivo de mensajes a borrar.", ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "No tienes permisos para borrar mensajes en este canal.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        mensajes_borrados = 0
        async for mensaje in interaction.channel.history(limit=cantidad):
            await mensaje.delete()
            mensajes_borrados += 1
            await asyncio.sleep(2)

        await interaction.followup.send(
            f"Se han borrado {mensajes_borrados} mensajes.", ephemeral=True
        )
    
    @app_commands.command(name="mute", description="Mutea a un usuario por un tiempo determinado")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time_minutes: int):
        # Verifica si el tiempo es menor a 2 minutos
        if time_minutes < 2:
            await interaction.response.send_message("El tiempo de muteo debe ser de al menos 2 minutos.", ephemeral=True)
            return
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
    
    @app_commands.command(name="registrar_usuarios", description="Registra a todos los usuarios del servidor en la base de datos")
    async def registrar_usuarios(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer para manejar la interacción

        # IDs de roles que corresponden a bots
        bot_roles_ids = {1213624079131746434, 1114642945094725767}

        # Obtener todos los miembros del servidor
        miembros = interaction.guild.members
        registrados = 0

        for miembro in miembros:
            # Verificar si el miembro tiene algún rol de bot
            tiene_rol_bot = any(role.id in bot_roles_ids for role in miembro.roles)

            if not tiene_rol_bot:  # Si no tiene roles de bot
                try:
                    # Usar conectar_db() para interactuar con la base de datos
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO usuarios (discord_id, nombre_usuario)
                        VALUES (?, ?)
                    ''', (str(miembro.id), miembro.name))
                    conn.commit()
                    registrados += 1
                    conn.close()
                except Exception as e:
                    print(f"Error al registrar a {miembro.name}: {e}")

        await interaction.followup.send(
            f"Se han registrado {registrados} usuarios en la base de datos.", ephemeral=True
        )

    
async def setup(client: commands.Bot):
    await client.add_cog(slash_commands(client))
