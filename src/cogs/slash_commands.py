import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import json
import requests
import os

def subir_a_imgur_directo(imagen_data, sancion_id):
    client_id = "7d95b2db396e96a"  # Tu Client ID de Imgur
    
    # Configurar los encabezados con el Client-ID
    headers = {
        'Authorization': f'Client-ID {client_id}'
    }
    
    # Parámetros opcionales para la imagen (título y descripción), ahora con la ID de la sanción en el título
    data = {
        'type': 'file',
        'title': f'Sanción de Discord #{sancion_id}',  # Usar la ID de la sanción
        'description': 'Imagen subida automáticamente desde el bot de Discord.'
    }
    
    # Realizar la solicitud POST para subir la imagen
    url = "https://api.imgur.com/3/image"
    files = {'image': imagen_data}
    
    response = requests.post(url, headers=headers, data=data, files=files)
    
    # Verificar la respuesta de la API
    if response.status_code == 200:
        # Si la subida fue exitosa, devolver la URL de la imagen
        response_data = response.json()
        return response_data['data']['link']
    else:
        print(f"Error al subir la imagen: {response.text}")
        return None
class slash_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client   
        # Cargar las URLs de gifs desde el archivo JSON
        with open(os.path.join("data", "media.json"), "r") as f:
            media_data = json.load(f)
            self.gifs = media_data.get("gifs", {})
            self.sanciones_file = os.path.join("data", "sanciones.json")
            self.sanciones = self.cargar_sanciones()
            self.sancion_id = self.obtener_ultima_id() + 1
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f"Comandos slash sincronizados en {len(self.client.guilds)} servidores.")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Comandos slash cargados correctamente.")
    
    @app_commands.command(name="serverip", description="Obtén la IP del servidor")
    async def serverip(self, interaction: discord.Interaction):
        await interaction.response.send_message("La IP del servidor es **server.boukencraft.com**", ephemeral=True)
    
    @app_commands.command(name="clear", description="Borra mensajes del canal")
    async def clear(self, interaction: discord.Interaction, amount: int):
        try:
            # Validar entrada
            if amount <= 0:
                await interaction.response.send_message(
                    "Por favor, introduce un número positivo mayor que 0.", ephemeral=True
                )
                return

            # Verificar permisos del bot
            if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
                await interaction.response.send_message(
                    "No tengo permisos para borrar mensajes en este canal.", ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)  # Responder mientras procesa

            # Borrar mensajes uno por uno con pausa
            count = 0
            async for message in interaction.channel.history(limit=amount):
                try:
                    await message.delete()
                    count += 1
                    await asyncio.sleep(2)  # Pausa de 2 segundos
                except discord.HTTPException as e:
                    print(f"Error HTTP al borrar un mensaje: {e}")
                    break

            # Respuesta final
            await interaction.followup.send(
                f"Se {'han' if count > 1 else 'ha'} borrado {count} mensaje{'s' if count > 1 else ''}.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "No tengo permisos para realizar esta acción.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                "Ocurrió un error al borrar los mensajes. Intenta nuevamente.", ephemeral=True
            )
            print(f"Error HTTP: {e}")
        except Exception as e:
            await interaction.followup.send(
                "Ocurrió un error inesperado.", ephemeral=True
            )
            print(f"Error inesperado: {e}")


    
    @app_commands.command(name="mute", description="Mutea a un usuario por un tiempo determinado")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time_minutes: int):
        # Verifica si el tiempo de muteo es mayor o igual a 2 minutos
        if time_minutes < 2:
            await interaction.response.send_message("El tiempo de muteo debe ser al menos de 2 minutos.", ephemeral=True)
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
        
        # Edita el mensaje en el canal de logs
        await initial_message.edit(content=f"{member.mention} fue muteado por {interaction.user.mention}. *Volvió a los {time_minutes} minutos*  :white_check_mark:")

    def cargar_sanciones(self):
        # Cargar las sanciones desde el archivo JSON
        if os.path.exists(self.sanciones_file):
            with open(self.sanciones_file, "r") as f:
                return json.load(f)
        return {}

    def guardar_sanciones(self):
        # Guardar las sanciones en el archivo JSON
        with open(self.sanciones_file, "w") as f:
            json.dump(self.sanciones, f, indent=4)


    def obtener_ultima_id(self):
        if not self.sanciones:
            return 0
        return max(int(sancion["id"]) for sanciones in self.sanciones.values() for sancion in sanciones)
        client_id = "7d95b2db396e96a"  # Tu Client ID de Imgur
        
        # Configurar los encabezados con el Client-ID
        headers = {
            'Authorization': f'Client-ID {client_id}'
        }
        
        # Abrir la imagen para enviarla
        with open(imagen_path, 'rb') as imagen:
            files = {
                'image': imagen.read()
            }
            
            # Parámetros opcionales para la imagen (título y descripción)
            data = {
                'type': 'file',
                'title': 'Sanción de Discord',
                'description': 'Imagen subida automáticamente desde el bot de Discord.'
            }
            
            # Realizar la solicitud POST para subir la imagen
            url = "https://api.imgur.com/3/image"
            response = requests.post(url, headers=headers, data=data, files=files)
            
            # Verificar la respuesta de la API
            if response.status_code == 200:
                # Si la subida fue exitosa, devolver la URL de la imagen
                response_data = response.json()
                return response_data['data']['link']
            else:
                print(f"Error al subir la imagen: {response.text}")
                return None

    @app_commands.command(name="sancionar", description="Sanciona a un jugador con un tipo de sanción específico")
    async def sancionar(self, interaction: discord.Interaction, member: discord.Member, tipo_sancion: str, imagen: discord.Attachment):
        tipos_permitidos = ["spam", "toxicidad", "flood", "off-topic"]
        rol_sancion = interaction.guild.get_role(1308823767820013658)
        
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

        # Verificar si la imagen es None y enviar un mensaje de error si es así
        if imagen is None:
            await interaction.response.send_message(
                "Es obligatorio proporcionar una imagen para la sanción.", ephemeral=True
            )
            return

        # Registrar la sanción
        user_id = str(member.id)
        if user_id not in self.sanciones:
            self.sanciones[user_id] = []
        
        sancion_id = self.sancion_id
        self.sancion_id += 1

        sancion = {
            "id": sancion_id,
            "motivo": tipo_sancion,
            "fecha": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "imagen": None
        }

        # Leer la imagen directamente desde el attachment
        imagen_data = await imagen.read()

        # Subir la imagen a Imgur y obtener la URL
        url_imagen = subir_a_imgur_directo(imagen_data, sancion_id)

        if url_imagen:
            sancion["imagen"] = url_imagen
        else:
            sancion["imagen"] = None

        self.sanciones[user_id].append(sancion)
        self.guardar_sanciones()

        await member.add_roles(rol_sancion)

        await interaction.response.send_message(
            f"{member.mention} ha sido sancionado por {tipo_sancion}. Total de sanciones: {len(self.sanciones[user_id])}", ephemeral=True
        )
    @app_commands.command(name="resetear_ids", description="Resetea las IDs de las sanciones (solo para testeo)")
    async def resetear_ids(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "No tienes permisos para resetear las IDs de las sanciones.", ephemeral=True
            )
            return

        self.sancion_id = 1
        await interaction.response.send_message("Las IDs de las sanciones han sido reseteadas.", ephemeral=True)

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


async def setup(client: commands.Bot) -> None:
    await client.add_cog(slash_commands(client))