import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
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
            self.sanciones_file = os.path.join("data", "sanciones.json")
            self.sanciones = self.cargar_sanciones()


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


    @app_commands.command(name="mute_message", description="Envía un mensaje al canal de mute")
    async def mute_message(self, interaction: discord.Interaction):
        channel_id = 1308131311034040340
        mention_channel_id = 1210343520582508634
        channel = interaction.guild.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("El canal no existe.", ephemeral=True)
            return
        
        # Verificar si ya existe un mensaje en el canal
        messages = [message async for message in channel.history(limit=1)]
        if messages:
            await interaction.response.send_message("Ya existe un mensaje en el canal.", ephemeral=True)
            return
        
        # Enviar el mensaje al canal y agregar la reacción
        message = await channel.send(f"# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE MUTEADO, ESPERA A QUE TERMINE EL TIMER PARA PODER CHARLAR NUEVAMENTE. REVISA TU MENCIÓN EN  <#{mention_channel_id}>")
        await message.add_reaction("😭")  # Reemplaza con :sob: si el emoji personalizado está disponible
        
        await interaction.response.send_message("Mensaje enviado al canal de mute.", ephemeral=True)
    
    # comando para crear sanction_message
    @app_commands.command(name="sanction_message", description="Envía un mensaje al canal de sanciones")
    async def sanction_message(self, interaction: discord.Interaction):
        channel_id = 1308814397321384081
        channel = interaction.guild.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("El canal no existe.", ephemeral=True)
            return
        
        # Verificar si ya existe un mensaje en el canal
        messages = [message async for message in channel.history(limit=1)]
        if messages:
            await interaction.response.send_message("Ya existe un mensaje en el canal.", ephemeral=True)
            return
        
        # Enviar el mensaje al canal y agregar la reacción
        message = await channel.send("# SI PUEDES VER ESTE CANAL SIGNIFICA QUE FUISTE SANCIONADO")
    
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

    @app_commands.command(name="sancionar", description="Sanciona a un jugador con un tipo de sanción específico")
    async def sancionar(self, interaction: discord.Interaction, member: discord.Member, tipo_sancion: str):
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

        # Registrar la sanción
        user_id = str(member.id)
        if user_id not in self.sanciones:
            self.sanciones[user_id] = []
        
        sancion = {
            "motivo": tipo_sancion,
            "fecha": datetime.now().strftime("%d-%m-%Y %H:%M")
        }
        self.sanciones[user_id].append(sancion)
        self.guardar_sanciones()
        
        await member.add_roles(rol_sancion)

        await interaction.response.send_message(
            f"{member.mention} ha sido sancionado por {tipo_sancion}. Total de sanciones: {len(self.sanciones[user_id])}", ephemeral=True
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


async def setup(client: commands.Bot) -> None:
    await client.add_cog(slash_commands(client))